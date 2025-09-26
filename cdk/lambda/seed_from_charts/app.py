import os
import re
import boto3

dynamodb = boto3.resource("dynamodb")

charts_table = dynamodb.Table(os.environ["CHARTS_TABLE"])
albums_table = dynamodb.Table(os.environ["ALBUMS_TABLE"])

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

def migrate_charts_to_albums():
    seen = set()
    count = 0
    scan_kwargs = {}

    while True:
        resp = charts_table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        print(f"📄 Processata pagina con {len(items)} elementi")

        for item in items:
            album_id = item.get("album_id")
            if not album_id:
                continue
            if album_id in seen:
                continue
            seen.add(album_id)

            title = (item.get("title") or "").strip()
            artist = (item.get("artist") or "").strip()
            release_date = item.get("release_date") or ""

            # tenta a derivare l'anno, ma non scrivere se non disponibile
            year_val = None
            if len(release_date) >= 4 and release_date[:4].isdigit():
                year_val = int(release_date[:4])

            # se esiste già, preserva rating e count
            existing = albums_table.get_item(Key={"album_id": album_id}).get("Item", {}) or {}
            avg_existing = existing.get("average_rating", 0)
            cnt_existing = existing.get("ratings_count", 0)

            album = {
                "album_id": album_id,
                "title": title,
                "title_lower": title.lower(),
                "title_slug": slugify(title),
                "artist": artist,
                "cover": item.get("cover", ""),
                "genre": item.get("genre", []),
                "songs": item.get("songs", []),
                "average_rating": avg_existing if isinstance(avg_existing, (int, float)) else 0,
                "ratings_count": cnt_existing if isinstance(cnt_existing, int) else 0,
            }
            if year_val is not None:
                album["year"] = year_val  # non inserire se None

            albums_table.put_item(Item=album)
            count += 1
            print(f"✅ Inserito/aggiornato album: {artist} – {title} ({album_id})")

        # continua se ci sono altre pagine
        lek = resp.get("LastEvaluatedKey")
        if lek:
            scan_kwargs["ExclusiveStartKey"] = lek
        else:
            break

    print(f"🎉 {count} album migrati da ChartsTable a AlbumsTable")
    return count

# 👉 Entry point per Lambda
def handler(event, context):
    try:
        count = migrate_charts_to_albums()
        return {
            "statusCode": 200,
            "body": f"{count} album migrati correttamente"
        }
    except Exception as e:
        print("❌ Errore:", e)
        return {
            "statusCode": 500,
            "body": str(e)
        }
