import boto3
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb")

# Nomi tabelle dalle variabili d'ambiente
users_table = dynamodb.Table(os.environ["USERS_TABLE"])
ratings_table = dynamodb.Table(os.environ["RATINGS_TABLE"])

def seed_users():
    users = [
        {
            "user_id": "user-123",
            "email": "alice@example.com",
            "favorites": ["a001"]
        },
        {
            "user_id": "user-456",
            "email": "bob@example.com",
            "favorites": ["a002"]
        }
    ]
    for user in users:
        users_table.put_item(Item=user)
    print("✅ Users inseriti")

def seed_ratings():
    ratings = [
        {
            "album_id": "a001",
            "user_id": "user-123",
            "rating": 5,
            "comment": "Capolavoro assoluto",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "album_id": "a002",
            "user_id": "user-456",
            "rating": 4,
            "comment": "Innovativo e profondo",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    for rating in ratings:
        ratings_table.put_item(Item=rating)
    print("✅ Ratings inseriti")

def handler(event, context):
    seed_users()
    seed_ratings()
    return {"statusCode": 200, "body": "🎉 Seed completato"}
