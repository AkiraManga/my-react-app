import boto3
import os
import json

sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

USERS_TABLE = os.environ["USERS_TABLE"]
TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

def handler(event, context):
    print("Evento ricevuto:", event)

    table = dynamodb.Table(USERS_TABLE)
    resp = table.scan()
    users = resp.get("Items", [])

    subscribed = []
    for user in users:
        email = user.get("email")
        if not email:
            continue

        sns.subscribe(
            TopicArn=TOPIC_ARN,
            Protocol="email",
            Endpoint=email
        )
        subscribed.append(email)

    return {
        "statusCode": 200,
        "body": json.dumps({"subscribed": subscribed})
    }
