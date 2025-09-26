import os, time, json, sys
from collections import defaultdict
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from decimal import Decimal

# -------- Config da ENV --------
CHARTS_TABLE       = os.environ["CHARTS_TABLE"]                    # 👈 usa CHARTS_TABLE
START_YEAR         = int(os.getenv("START_YEAR", "1970"))
END_YEAR           = int(os.getenv("END_YEAR", "2025"))
PER_MARKET_FETCH   = int(os.getenv("PER_MARKET_FETCH", "100"))     # paging a blocchi max 50
TOP_K              = int(os.getenv("TOP_K", "20"))
SLEEP_BETWEEN_CALL = float(os.getenv("SLEEP_BETWEEN_CALL", "0.25"))

# Definizione gruppi/regioni → lista mercati Spotify
EUROPE_MARKETS = ["IT","FR","DE","ES","NL","SE","GB","IE","PT","BE","AT","CH","DK","NO","FI","GR","PL","CZ","HU","RO","SK","SI","HR","BG","LT","LV","EE","LU","MT","CY"]
US_MARKETS     = ["US"]
IT_MARKETS     = ["IT"]

# Se vuoi aggiungere regioni, basta estendere questo dict
REGION_GROUPS = {
    "GLOBAL": None,        # speciale: somma/medie su TUTTI i mercati che trovi nella ricerca globale
    "EUROPE": EUROPE_MARKETS,
    "US": US_MARKETS,
    "IT": IT_MARKETS,
}

# -------- Clients --------
dynamodb = boto3.resource("dynamodb")
charts = dynamodb.Table(CHARTS_TABLE)

sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["SPOTIPY_CLIENT_ID"],
    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"]
))

# -------- Helpers --------
def _retryable(fn, *args, **kwargs):
    backoff = 0.5
    for attempt in range(7):
        try:
            return fn(*args, **kwargs)
        except SpotifyException as e:
            status = getattr(e, "http_status", None)
            if status in (429, 500, 502, 503, 504):
                retry_after = getattr(e, "headers", {}).get("Retry-After")
                wait = float(retry_after) if retry_after else backoff
                wait = min(wait, 15.0)
                print(f"⏳ Spotify {status}, retry tra {wait}s...", flush=True)
                time.sleep(wait)
                backoff = min(backoff * 2, 15.0)
                continue
            raise
        except Exception:
            if attempt < 6:
                time.sleep(backoff)
                backoff = min(backoff * 2, 10.0)
                continue
            raise

def search_albums_year_market(year: int, market: str, want: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    remaining = want
    offset = 0
    while remaining > 0:
        limit = min(remaining, 50)
        res = _retryable(
            sp.search,
            q=f"year:{year}",
            type="album",
            limit=limit,
            offset=offset,
            market=market
        ) or {}
        batch = (res.get("albums") or {}).get("items", [])
        if not batch:
            break
        items.extend(batch)
        remaining -= len(batch)
        offset += len(batch)
        time.sleep(SLEEP_BETWEEN_CALL)
        if len(batch) < limit:
            break
    return items

def aggregate_for_markets(year: int, markets: List[str] | None, per_market_fetch: int) -> Dict[str, Dict[str, Any]]:
    """
    Ritorna un dict album_id -> {sum, n, album, markets:set}
    Se markets è None: usa un insieme di mercati “proxy” prendendo market=None (GLOBAL-like).
    """
    agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"sum": 0.0, "n": 0, "album": None, "markets": set()})
    # Caso GLOBAL: facciamo una sola ricerca senza 'market' e usiamo popularity del payload (se presente)
    if markets is None:
        # spotipy non consente search senza mercato? Allora usiamo un mercato “ampio”
        markets = ["US","GB","DE","FR","IT","BR","MX","JP","AU","CA","ES","NL","SE"]

    for m in markets:
        try:
            print(f"📡 {year} – fetch market {m}...", flush=True)
            items = search_albums_year_market(year, m, per_market_fetch)
            for alb in items:
                if alb.get("album_type") != "album":
                    continue
                rd = (alb.get("release_date") or "")[:4]
                if rd != str(year):
                    continue
                aid = alb.get("id")
                if not aid:
                    continue
                pop = alb.get("popularity") or 0
                agg[aid]["sum"] += float(pop)
                agg[aid]["n"] += 1
                agg[aid]["album"] = alb
                agg[aid]["markets"].add(m)
        except Exception as e:
            print(f"⚠️ {year} market {m}: {e}", flush=True)
    return agg

def build_chart_entries(year: int, agg: Dict[str, Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    ranked = []
    for aid, a in agg.items():
        alb = a["album"]
        if not alb or a["n"] == 0:
            continue
        artist = (alb.get("artists") or [{}])[0].get("name", "Unknown")
        ranked.append({
            "album_id": aid,
            "title": alb.get("name"),
            "artist": artist,
            "release_date": alb.get("release_date", ""),
            "cover": (alb.get("images") or [{}])[0].get("url", ""),
        })

    # dedup su (artist, title)
    seen = set()
    deduped = []
    for r in ranked:   # 👈 non serve più ordinare per score
        key = (r["artist"].lower(), r["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
        if len(deduped) >= top_k:
            break
    return deduped




def get_album_details(album_id: str) -> Dict[str, Any]:
    """Recupera solo le tracce di un album da Spotify"""
    try:
        alb = _retryable(sp.album, album_id)
        if not alb:
            return {}
        return {
            "songs": [t.get("name") for t in alb.get("tracks", {}).get("items", [])]
        }
    except Exception as e:
        print(f"⚠️ Dettagli album {album_id} non trovati: {e}", flush=True)
        return {"songs": []}

    

def save_chart(year: int, entries: List[Dict[str, Any]]):
    chart_key = str(year)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    seen_ids = set()
    with charts.batch_writer() as batch:
        for idx, e in enumerate(entries, start=1):
            if e["album_id"] in seen_ids:
                print(f"⚠️ Skip duplicato: {e['artist']} – {e['title']} (id={e['album_id']})", flush=True)
                continue
            seen_ids.add(e["album_id"])

            details = get_album_details(e["album_id"])

            item = {
                "chart_key": chart_key,   # PK = anno
                "rank": idx,              # SK
                "year": year,
                "album_id": e["album_id"],
                "title": e["title"],
                "artist": e["artist"],
                "release_date": e.get("release_date", ""),
                "cover": e.get("cover", ""),
                "source": "spotify",
                "fetched_at": ts,
                "songs": details.get("songs", []),
            }
            batch.put_item(Item=item)
            print(f"✅ {year} #{idx}: {e['artist']} – {e['title']}", flush=True)



def run_for_year(year: int):
    print(f"🧮 Aggrego {year}", flush=True)
    # lista mercati fissi per avere un po' di diversità
    markets = ["US","GB","DE","FR","IT"]
    agg = aggregate_for_markets(year, markets, PER_MARKET_FETCH)
    entries = build_chart_entries(year, agg, TOP_K)
    save_chart(year, entries)






def main():
    print(f"▶️ RUN years {START_YEAR}-{END_YEAR} | per_market_fetch={PER_MARKET_FETCH} | top_k={TOP_K}", flush=True)
    for year in range(START_YEAR, END_YEAR + 1):
        run_for_year(year)

if __name__ == "__main__":
    try:
        main()
    except KeyError as ke:
        print(f"❌ Env var mancante: {ke}. Controlla SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, CHARTS_TABLE.", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Errore fatale: {e}", file=sys.stderr)
        sys.exit(1)
