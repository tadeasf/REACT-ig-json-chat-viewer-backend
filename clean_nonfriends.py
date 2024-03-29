import os
import json
import shutil


def move_subdirectories_based_on_conditions(source_dir, target_dir):
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        # Check if the item is a directory
        if os.path.isdir(item_path):
            message_file = os.path.join(item_path, "message_1.json")
            # Check if message_1.json exists in this subdirectory
            if os.path.isfile(message_file):
                with open(message_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    # Count the number of messages and participants
                    message_count = len(data.get("messages", []))
                    participants_count = len(data.get("participants", []))
                    # Move the directory if message count is less than 1500
                    # or if participants count is more than 2
                    if message_count < 1500 or participants_count > 2:
                        target_subdir = os.path.join(target_dir, item)
                        # Ensure not to overwrite existing directories in target
                        if not os.path.exists(target_subdir):
                            shutil.move(item_path, target_subdir)
                            print(f"Moved {item_path} to {target_subdir}")
                        else:
                            print(
                                f"Target directory {target_subdir} already exists. Consider renaming or manually handling."
                            )


# Example usage
source_directory = "/root/REACT-ig-json-chat-viewer-backend/inbox"
target_directory = "/root/meta_backup"
move_subdirectories_based_on_conditions(source_directory, target_directory)
