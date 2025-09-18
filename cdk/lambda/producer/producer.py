import boto3
import os

sqs = boto3.client("sqs")
queue_url = os.environ["QUEUE_URL"]

def handler(event, context):
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody="Nuovo messaggio da Cognito app!"
    )
    return {
        "statusCode": 200,
        "body": "Messaggio inviato a SQS"
    }
