# lambda/charts_read/app.py
import os, json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CHARTS_TABLE"])

def _dec(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError

def _cors():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
    }

def handler(event, context):
    try:
        path = event.get("resource") or ""
        params = event.get("pathParameters") or {}

        # Supporta /charts/{year} e /charts/{region}/{year}
        if path in ("/charts/{year}", "/charts/{region}/{year}"):
            year = str(params.get("year") or "").strip()
        else:
            return {"statusCode": 404, "headers": _cors(),
                    "body": json.dumps({"error": "Endpoint non trovato"})}

        if not year.isdigit():
            return {"statusCode": 400, "headers": _cors(),
                    "body": json.dumps({"error": "Anno non valido"})}

        # 1) Nuovo schema: chart_key == "1971"
        resp = table.query(
            KeyConditionExpression=Key("chart_key").eq(year),
            ScanIndexForward=True  # rank crescente
        )
        items = resp.get("Items", [])

        # 2) Fallback compat vecchio schema: chart_key == "1971#EUROPE" / "1971#US" ecc.
        if not items:
            scan_kwargs = {"FilterExpression": Attr("chart_key").begins_with(f"{year}#")}
            items = []
            lek = None
            while True:
                if lek:
                    scan_kwargs["ExclusiveStartKey"] = lek
                s = table.scan(**scan_kwargs)
                items.extend(s.get("Items", []))
                lek = s.get("LastEvaluatedKey")
                if not lek:
                    break

            if not items:
                return {"statusCode": 404, "headers": _cors(),
                        "body": json.dumps({"error": f"No chart for year {year}"})}

        # Ordina per rank e ripulisci campi legacy
        items.sort(key=lambda x: x.get("rank", 10**9))
        for it in items:
            it.pop("region", None)
            it.pop("fetched_at", None)

        return {"statusCode": 200, "headers": _cors(),
                "body": json.dumps({"items": items}, default=_dec)}

    except Exception as e:
        return {"statusCode": 500, "headers": _cors(),
                "body": json.dumps({"error": str(e)})}
