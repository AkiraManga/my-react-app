def handler(event, context):
    for record in event["Records"]:
        print("Messaggio ricevuto:", record["body"])
    return {"statusCode": 200}
