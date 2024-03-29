import os
import shutil

def flatten_directory(source, target, remove_original=False):
    """
    Recursively move files from source directory to target directory, flattening the structure.
    
    Args:
    - source: The source directory to move files from.
    - target: The target directory to move files to.
    - remove_original: Whether to remove the original source directory after moving files.
    """
    for root, dirs, files in os.walk(source):
        # Calculate the relative path from the source directory to use in the target directory
        relative_path = os.path.relpath(root, source)
        target_path = os.path.join(target, relative_path)
        
        # Ensure the target directory exists
        os.makedirs(target_path, exist_ok=True)
        
        # Move each file to the new target directory
        for file in files:
            src_file_path = os.path.join(root, file)
            dst_file_path = os.path.join(target_path, file)
            shutil.move(src_file_path, dst_file_path)
            print(f"Moved: {src_file_path} -> {dst_file_path}")
    
    # Optionally, remove the original source directory
    if remove_original:
        shutil.rmtree(os.path.join(source, "..", "messages"))
        print(f"Removed original directory: {os.path.join(source, '..', 'messages')}")

# Define your paths
source_dir = "/root/REACT-ig-json-chat-viewer-backend/inbox/your_activity_across_facebook/messages/inbox/"
target_dir = "/root/REACT-ig-json-chat-viewer-backend/inbox/your_activity_across_facebook/"

# Call the function
flatten_directory(source_dir, target_dir, remove_original=True)

