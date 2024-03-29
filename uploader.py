import os
import json
import requests

root_dir = "/root/REACT-ig-json-chat-viewer-backend/inbox"


def is_valid_json(file_path):
    """Check if the file contains valid JSON and meets the participant criteria."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        if len(data.get("participants", [])) >= 2:
            return True
        else:
            print(f"Invalid participant count in {file_path}")
            return False
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error in {file_path}: {str(e)}")
        return False


# Function to upload files
def upload_files(subdir, files_to_upload):
    if files_to_upload:
        print(f"Uploading files in subdirectory: {subdir}")
        try:
            response = requests.post(
                "https://secondary.dev.tadeasfort.com/upload", files=files_to_upload
            )
            response.raise_for_status()  # This will raise an exception for HTTP error codes
            print(f"Response from server: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error occurred during upload: {e}")
        finally:
            # Correctly close the file handles
            for _, file_tuple in files_to_upload:
                file_object = file_tuple[1]  # Extract the file object from the tuple
                file_object.close()


# Iterate over all subdirectories in the root directory
for subdir, dirs, files in os.walk(root_dir):
    if not any(file.startswith("message_") for file in files):
        print(f"Skipping subdirectory with no message files: {subdir}")
        continue

    # Prepare a list to hold file tuples for uploading
    files_to_upload = []

    for file in files:
        if file.startswith("message_") and is_valid_json(os.path.join(subdir, file)):
            file_path = os.path.join(subdir, file)
            # Open the file in binary mode for uploading
            file_to_upload = open(file_path, "rb")
            files_to_upload.append(("files", (file, file_to_upload)))

    # Upload all collected files in a single request
    upload_files(subdir, files_to_upload)
