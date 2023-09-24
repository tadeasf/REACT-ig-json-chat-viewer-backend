from pymongo import MongoClient


def move_collections(uri, input_db_name, output_db_name, collection_names):
    # Connect to MongoDB
    client = MongoClient(uri)

    # Access the input and output databases
    input_db = client[input_db_name]
    output_db = client[output_db_name]

    for collection_name in collection_names:
        # Check if the collection exists in the input database
        if collection_name in input_db.list_collection_names():
            # Get the input and output collections
            input_collection = input_db[collection_name]
            output_collection = output_db[collection_name]

            # Copy documents from the input collection to the output collection
            for document in input_collection.find({}):
                output_collection.insert_one(document)

            # Remove the collection from the input database
            input_db.drop_collection(collection_name)

            print(
                f"Moved collection {collection_name} from {input_db_name} to {output_db_name}"
            )
        else:
            print(f"Collection {collection_name} does not exist in {input_db_name}")


if __name__ == "__main__":
    uri = "mongodb://supertadeas:%24803k%40Xa%25yFfufA%23505wq%2F%40%5D%5D@mongodb.kocouratko.eu:27017/messages?authSource=admin"
    input_db_name = "kocouratciMessenger"
    output_db_name = "kocouratciMessengerBackup"
    collection_names = [
        "collection1",
        "collection2",
        "collection3",
    ]  # Replace with your collection names

    move_collections(uri, input_db_name, output_db_name, collection_names)
