import os
import json
import boto3
from decimal import Decimal
import urllib.parse
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
albums_table = dynamodb.Table(os.environ["ALBUMS_TABLE"])


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
    }


def handler(event, context):
    try:
        path = event.get("resource")
        path_params = event.get("pathParameters", {}) or {}

        # ✅ GET /albums/by-title/{title}
        if path == "/albums/by-title/{title}":
            raw = (path_params.get("title") or "").strip()
            if not raw:
                return {"statusCode": 400, "headers": cors_headers(),
                        "body": json.dumps({"error": "Titolo mancante"})}

            decoded = urllib.parse.unquote(raw)
            title_norm = decoded.lower()

            resp = albums_table.query(
                IndexName="TitleLowerIndex",
                KeyConditionExpression=Key("title_lower").eq(title_norm)
            )
            items = resp.get("Items", [])
            if not items:
                return {"statusCode": 404, "headers": cors_headers(),
                        "body": json.dumps({"error": "Album non trovato"})}
            return {"statusCode": 200, "headers": cors_headers(),
                    "body": json.dumps(items, default=decimal_default)}

        # ✅ GET /albums/by-slug/{slug}
        if path == "/albums/by-slug/{slug}":
            raw = (path_params.get("slug") or "").strip()
            if not raw:
                return {"statusCode": 400, "headers": cors_headers(),
                        "body": json.dumps({"error": "Slug mancante"})}

            decoded = urllib.parse.unquote(raw)
            slug_norm = decoded.lower()

            resp = albums_table.query(
                IndexName="TitleSlugIndex",
                KeyConditionExpression=Key("title_slug").eq(slug_norm)
            )
            items = resp.get("Items", [])
            if not items:
                return {"statusCode": 404, "headers": cors_headers(),
                        "body": json.dumps({"error": "Album non trovato"})}
            return {"statusCode": 200, "headers": cors_headers(),
                    "body": json.dumps(items[0], default=decimal_default)}

        # ✅ GET /albums/{id}
        if path == "/albums/{id}":
            album_id = path_params.get("id") or path_params.get("album_id")
            if not album_id:
                return {"statusCode": 400, "headers": cors_headers(),
                        "body": json.dumps({"error": "Album ID mancante"})}
            response = albums_table.get_item(Key={"album_id": album_id})
            item = response.get("Item")
            if not item:
                return {"statusCode": 404, "headers": cors_headers(),
                        "body": json.dumps({"error": "Album non trovato"})}
            return {"statusCode": 200, "headers": cors_headers(),
                    "body": json.dumps(item, default=decimal_default)}

        # ✅ GET /albums (listing base)
        if path == "/albums":
            response = albums_table.scan()
            items = response.get("Items", [])
            return {"statusCode": 200, "headers": cors_headers(),
                    "body": json.dumps(items, default=decimal_default)}

        return {"statusCode": 404, "headers": cors_headers(),
                "body": json.dumps({"error": "Endpoint non trovato"})}

    except Exception as e:
        return {"statusCode": 500, "headers": cors_headers(),
                "body": json.dumps({"error": str(e)})}
