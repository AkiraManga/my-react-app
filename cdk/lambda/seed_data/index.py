import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb")

# Nomi tabelle dalle variabili d'ambiente
albums_table = dynamodb.Table(os.environ["ALBUMS_TABLE"])
users_table = dynamodb.Table(os.environ["USERS_TABLE"])
ratings_table = dynamodb.Table(os.environ["RATINGS_TABLE"])

def seed_albums():
    with open("albums.json") as f:
        data = json.load(f)["Albums"]

    for album in data:
        item = album["PutRequest"]["Item"]
        clean_item = {}
        for k, v in item.items():
            if "S" in v:
                clean_item[k] = v["S"]
            elif "N" in v:
                clean_item[k] = int(v["N"])
            elif "L" in v:
                clean_item[k] = [x["S"] for x in v["L"]]
        albums_table.put_item(Item=clean_item)

    print(f"✅ {len(data)} albums inseriti")

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
    seed_albums()
    seed_users()
    seed_ratings()
    return {"statusCode": 200, "body": "🎉 Seed completato"}
