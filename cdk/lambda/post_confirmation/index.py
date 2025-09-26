import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE"])

sns = boto3.client("sns")
TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

def handler(event, context):
    user_id = event["userName"]  # Cognito sub
    email = event["request"]["userAttributes"].get("email")

    # Inserisci solo se non esiste già
    try:
        table.put_item(
            Item={
                "user_id": user_id,
                "email": email
                # ⚠️ niente favorites qui!
            },
            ConditionExpression="attribute_not_exists(user_id)"
        )
        print(f"User {user_id} inserted in DynamoDB")
    except Exception as e:
        print(f"User {user_id} already exists or error: {e}")

    # --- Nuova parte: iscrizione SNS ---
    if email:
        try:
            sns.subscribe(
                TopicArn=TOPIC_ARN,
                Protocol="email",
                Endpoint=email
            )
            print(f"Email {email} sottoscritta a {TOPIC_ARN}")
        except Exception as e:
            print(f"Errore iscrizione SNS per {email}: {e}")

    return event
