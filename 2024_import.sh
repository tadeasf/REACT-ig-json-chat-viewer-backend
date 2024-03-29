#!/bin/bash

# Define the output (destination) directory
DESTINATION_DIR="/root/REACT-ig-json-chat-viewer-backend/inbox"

# Array of input (source) directories
SOURCE_DIRS=(
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-7n4RTVJl/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-AyfjSqnR/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-b8kvTWSF/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-ThvmOrqC/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-cziIAEXu/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-qIZxqSr6/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-w8qJTahW/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/facebook-TadeasFort-2024-03-25-WIO9twEv/your_activity_across_facebook/messages/inbox"
  "/root/REACT-ig-json-chat-viewer-backend/meta_data/instagram-whostoletedsusername-2024-03-25-Pf75u8Wp/your_instagram_activity/messages/inbox"
)

# Loop through the source directories and use rsync to copy each to the destination
for SOURCE_DIR in "${SOURCE_DIRS[@]}"; do
  echo "Syncing $SOURCE_DIR to $DESTINATION_DIR"
  rsync -av "$SOURCE_DIR/" "$DESTINATION_DIR/"
done

echo "All directories have been synced."

