import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE"])

def handler(event, context):
    user_id = event["userName"]  # Cognito sub
    email = event["request"]["userAttributes"].get("email")

    # Inserisci solo se non esiste già
    try:
        table.put_item(
            Item={
                "user_id": user_id,
                "email": email,
                "favorites": []
            },
            ConditionExpression="attribute_not_exists(user_id)"
        )
        print(f"User {user_id} inserted in DynamoDB")
    except Exception as e:
        print(f"User {user_id} already exists or error: {e}")

    return event
