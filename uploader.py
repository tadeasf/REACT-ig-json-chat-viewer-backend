import os
import requests
import json
import time

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


# Iterate over all subdirectories in the root directory
for subdir, dirs, files in os.walk(root_dir):
    # Filter files that start with "message_"
    message_files = [file for file in files if file.startswith("message_")]
    # Skip subdirectories with no message files
    if not message_files:
        continue
    # Skip subdirectories with only one message file that has less than 2500 lines
    if len(message_files) == 1:
        with open(os.path.join(subdir, message_files[0]), "r") as f:
            lines = f.readlines()
            if len(lines) < 2500:
                print(
                    f"Skipping subdirectory: {subdir} (message file has less than 2500 lines)"
                )
                continue
    # Upload all message files in the subdirectory
    print(f"Uploading files in subdirectory: {subdir}")
    # Adjust here to use the "files" field name
    # Further filter to keep only valid JSON files
    valid_message_files = [
        file for file in message_files if is_valid_json(os.path.join(subdir, file))
    ]

    # Skip subdirectories with no valid JSON message files
    if not valid_message_files:
        print(f"Skipping subdirectory: {subdir} (no valid JSON message files)")
        continue

    for file in valid_message_files:
        with open(os.path.join(subdir, file), "rb") as file_to_upload:
            try:
                print("calling the endpoint")
                response = requests.post(
                    "https://secondary.dev.tadeasfort.com/upload",
                    files={"files": (file, file_to_upload)},
                )
                response.raise_for_status()
                print(f"Response from server: {response.text}")
            except requests.exceptions.HTTPError as http_err:
                # Check if the error is one of the specified types
                if response.status_code not in [200, 202]:
                    print(
                        f"HTTP error occurred: {http_err} - Status code: {response.status_code}"
                    )
                    print("Waiting for 10 seconds before retrying...")
                    with open("error_log.txt", "a") as log_file:
                        log_file.write(
                            f"Directory: {subdir}\n"
                            f"Error occurred: {http_err} - Status code: {response.status_code}\n"
                        )
                    time.sleep(10)
                    # Optionally, you might want to retry the request here or just continue to the next file
                else:
                    print(
                        f"Other HTTP error occurred: {http_err} - Status code: {response.status_code}"
                    )
            except requests.exceptions.RequestException as err:
                print(f"Request error: {err}")
            finally:
                # The file is automatically closed when exiting the 'with' block
                pass
