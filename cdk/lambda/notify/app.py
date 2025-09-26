import os
import json
import boto3

ses = boto3.client("ses", region_name="eu-west-3")  # usa la tua regione SES
SOURCE_EMAIL = os.environ["SES_SOURCE_EMAIL"]

def handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        to_email = body.get("to_email")
        message = body.get("message")

        if not to_email or not message:
            return response(400, {"error": "Missing to_email or message"})

        # Invia email
        ses.send_email(
            Source=SOURCE_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": "Notifica dal tuo album"},
                "Body": {
                    "Text": {"Data": message}
                }
            }
        )

        return response(200, {"status": "Email inviata con successo"})

    except Exception as e:
        print("Errore SES:", str(e))
        return response(500, {"error": str(e)})


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(body)
    }
