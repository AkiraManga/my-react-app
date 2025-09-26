import os, time
from collections import defaultdict
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

YEAR = 2025
LIMIT = 10
GLOBAL_MARKETS = ["US","GB","DE","FR","IT","ES","NL","SE","BR","MX","JP","AU","CA"]

sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ["SPOTIPY_CLIENT_ID"],
    client_secret=os.environ["SPOTIPY_CLIENT_SECRET"]
))

def search_tracks_year_market(year, market, want=60, sleep=0.25):
    """Cerca tracce per anno/market, rispettando limit<=50 con paging."""
    got = []
    remaining = want
    offset = 0
    while remaining > 0:
        batch = min(remaining, 50)  # limite API
        res = sp.search(q=f"year:{year}", type="track", limit=batch, offset=offset, market=market) or {}
        items = (res.get("tracks") or {}).get("items", [])
        if not items:
            break
        got.extend(items)
        remaining -= len(items)
        offset += len(items)
        time.sleep(sleep)
        if len(items) < batch:
            break
    return got

def top_albums_by_year(markets, year, per_market_fetch=50, limit=10):
    album_scores = defaultdict(lambda: {"sum":0, "n":0, "album":None})
    for m in markets:
        try:
            items = search_tracks_year_market(year, m, want=per_market_fetch)
            for tr in items:
                pop = tr.get("popularity") or 0
                alb = tr.get("album") or {}
                # filtra riedizioni o compilation: tieni solo release_date nell'anno
                if (alb.get("release_date") or "")[:4] != str(year):
                    continue
                aid = alb.get("id")
                if not aid: 
                    continue
                album_scores[aid]["sum"] += pop
                album_scores[aid]["n"] += 1
                album_scores[aid]["album"] = alb
        except SpotifyException as e:
            print(f"⚠️ market {m}: {e}")

    ranked = []
    for aid, agg in album_scores.items():
        if not agg["album"]: 
            continue
        mean = agg["sum"] / max(1, agg["n"])
        alb = agg["album"]
        artist = (alb.get("artists") or [{}])[0].get("name", "Sconosciuto")
        ranked.append({
            "album_id": aid,
            "title": alb.get("name"),
            "artist": artist,
            "year": str(year),
            "score": round(mean, 1),
            "cover": (alb.get("images") or [{}])[0].get("url", "")
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]

if __name__ == "__main__":
    it = top_albums_by_year(["IT"], YEAR, per_market_fetch=50, limit=LIMIT)
    print(f"🇮🇹 Top {LIMIT} Italia – {YEAR}:")
    for i, a in enumerate(it, 1):
        print(f"{i:2d}. {a['artist']} — {a['title']} (score {a['score']})")

    print()
    gl = top_albums_by_year(GLOBAL_MARKETS, YEAR, per_market_fetch=50, limit=LIMIT)
    print(f"🌍 Top {LIMIT} Globale (proxy) – {YEAR}:")
    for i, a in enumerate(gl, 1):
        print(f"{i:2d}. {a['artist']} — {a['title']} (score {a['score']})")
