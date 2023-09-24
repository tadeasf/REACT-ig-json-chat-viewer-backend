from pymongo import MongoClient
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import os
import pymongo.errors


def copy_collection(input_db, output_db, collection_name):
    # Get the input and output collections
    input_collection = input_db[collection_name]
    output_collection = output_db[collection_name]

    # Fetch all documents and prepare for bulk insert
    documents = list(input_collection.find({}))
    for document in documents:
        document.pop("_id", None)

    # Bulk insert into the output collection
    if documents:
        output_collection.insert_many(documents)

    print(f"Copied collection {collection_name}")


def copy_database(uri, input_db_name, output_db_name):
    try:
        # Connect to MongoDB
        client = MongoClient(uri)

        # Access the input and output databases
        input_db = client[input_db_name]
        output_db = client[output_db_name]

        # Fetch all collections from the input database
        collection_names = input_db.list_collection_names()

        # Using ThreadPoolExecutor to copy collections in parallel
        with ThreadPoolExecutor() as executor:
            list(
                tqdm(
                    executor.map(
                        lambda x: copy_collection(input_db, output_db, x),
                        collection_names,
                    ),
                    total=len(collection_names),
                    desc="Collections",
                )
            )
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print(f"Failed to connect to MongoDB: {e}")
    except pymongo.errors.OperationFailure as e:
        print(f"Operation failed: {e}")


if __name__ == "__main__":
    uri = "mongodb://supertadeas:%24803k%40Xa%25yFfufA%23505wq%2F%40%5D%5D@mongodb.kocouratko.eu:27017/messages?authSource=admin"
    input_db_name = "kocouratciMessenger"
    output_db_name = "kocouratciMessengerBackup"

    copy_database(uri, input_db_name, output_db_name)
