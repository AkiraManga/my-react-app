import json

def handler(event, context):
    body = json.loads(event.get("body", "{}"))
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Favorites Lambda in Docker funziona!", "data": body})
    }
