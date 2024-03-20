import pandas as pd
from pymongo import MongoClient


def run_aggregation_and_export_to_csv(mongo_uri, db_name):
    client = MongoClient(mongo_uri)
    db = client[db_name]

    pipeline = [
        {"$sort": {"timestamp_ms": 1}},
        {
            "$project": {
                "reactions": 0,
                "audio_files": 0,
                "files": 0,
                "gifs": 0,
                "share": 0,
                "sticker": 0,
            }
        },
        {"$unwind": {"path": "$photos", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 1,
                "sender_id_INTERNAL": 1,
                "sender_name": 1,
                "timestamp_ms": 1,
                "timestamp": 1,
                "content": 1,
                "sanitizedContent": 1,
                "photo_creation_timestamp": "$photos.creation_timestamp",
                "photo_uri": "$photos.uri",
            }
        },
    ]

    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        results = collection.aggregate(pipeline)
        df = pd.DataFrame(list(results))

        if not df.empty:
            # Convert ObjectId to string for CSV compatibility
            df["_id"] = df["_id"].astype(str)
            csv_file_name = f"/root/REACT-ig-json-chat-viewer-backend/python_mysql_migration/csvs/{collection_name}.csv"
            df.to_csv(csv_file_name, index=False)
            print(f"Exported {collection_name} to {csv_file_name}")
        else:
            print(f"No data to export from {collection_name}")


if __name__ == "__main__":
    mongo_uri = input("Enter MongoDB URI: ")
    db_name = input("Enter Database Name: ")
    run_aggregation_and_export_to_csv(mongo_uri, db_name)
