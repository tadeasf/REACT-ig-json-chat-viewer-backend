from pymongo import MongoClient
import concurrent.futures
import time
from random import choice
from mongo_daytripdb_contabovps_pipelines import pipelines as get_pipelines
from typing import Dict, List
import os
import threading
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB
def connect_to_mongodb(uri, db_name):
    client = MongoClient(uri, maxPoolSize=50, minPoolSize=10)
    db = client[db_name]
    return db

# Function to ensure the directory exists and create it if not
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to get the dynamic file name based on the current time
def get_dynamic_file_name():
    current_time_str = time.strftime("%H-%M-%S_%d-%m-%Y", time.localtime())
    return f"torturing_mongodb_{current_time_str}.json"

# Initialize a lock
lock = threading.Lock()

# Function to append data to a JSON file
def append_to_json(file_path, data):
    with lock:
        with open(file_path, 'r+') as file:
            file_data = json.load(file)
            file_data.append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)

# Function to execute the pipeline
def execute_pipeline(collection, pipeline, pipeline_name, file_path):
    try:
        start_time = time.time()
        start_str = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(start_time))
        data = list(collection.aggregate(pipeline, allowDiskUse=True))
        end_time = time.time()
        end_str = time.strftime("%H:%M:%S %d/%m/%Y", time.localtime(end_time))
        execution_time = end_time - start_time

        data = {
            'aggregationPipelineName': pipeline_name,
            'collection': collection.name,
            'startTime': start_str,
            'endTime': end_str,
            'executionTime': execution_time
        }

        # Append data to JSON file
        append_to_json(file_path, data)
    except Exception as e:
        print(f"Error executing pipeline on {collection.name}: {str(e)}")

# Simulate user load on the database
def simulate_user_load(db, pipelines: Dict[str, List[dict]], run_time, concurrent_aggregations):
    
    ensure_directory_exists('torture-data')
    file_name = get_dynamic_file_name()
    file_path = os.path.join('torture-data', file_name)

    # Initial setup for JSON file
    file_data: List[dict] = []
    with open(file_path, 'w') as file:
        json.dump(file_data, file, indent=4)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_aggregations) as executor:
        futures = []
        start_time = time.time()
        
        while True:
            pipeline_key, pipeline = choice(list(pipelines.items()))
            pipeline_name, collection_name = pipeline_key.split('_', 1)
            collection = db[collection_name]
            future = executor.submit(
                execute_pipeline,
                collection,
                pipeline,
                pipeline_name,
                file_path
            )
            futures.append(future)

            if run_time and (time.time() - start_time) > run_time:
                break
            time.sleep(1)

        # Wait for all futures to complete
        concurrent.futures.wait(futures)

# Get user input for simulation parameters
def get_user_input():
    run_time = input("Enter how long to run in seconds (optional, press enter to run indefinitely): ")
    concurrent_aggregations = int(input("Enter the number of concurrent aggregations: "))

    if run_time:
        run_time = int(run_time)
    else:
        run_time = None

    return run_time, concurrent_aggregations

# Main function to run the script
def main():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    db = connect_to_mongodb(uri, db_name)

    # Get the dictionary of pipelines by calling the function
    pipelines_dict = get_pipelines()

    run_time, concurrent_aggregations = get_user_input()
    simulate_user_load(db, pipelines_dict, run_time, concurrent_aggregations)

if __name__ == "__main__":
    main()