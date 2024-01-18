#!/bin/bash

# Check if $caddy_user is set, if not, ask for the Caddy user
if [ -z "$caddy_user" ]; then
    read -p "Enter the Caddy user name: " caddy_user
else
    echo "Using Caddy user from caddy_user environment variable: $caddy_user"
fi

# Ask for the GitHub path in the format "user/repo"
read -p "Enter the GitHub path (format: user/repo): " github_path

# Construct the full GitHub repository URL
REPO_URL="https://github.com/$github_path"

# Get the home directory of the Caddy user
CADDY_HOME=$(eval echo ~$caddy_user)

# Extract just the repository name from the path
github_repo=$(basename $github_path)

# Clone the repository in the Caddy user's home directory
sudo su - $caddy_user -c "git clone $REPO_URL $CADDY_HOME/$github_repo"

# Navigate to the repository and build the React app
sudo su - $caddy_user -c "cd $CADDY_HOME/$github_repo && npm install && npm run build"

# Output suggested Caddyfile configuration
echo "Add the following configuration to your Caddyfile:"
echo "http://your_domain.com {"
echo "    root * $CADDY_HOME/$github_repo/build"
echo "    file_server"
echo "    try_files {path} /index.html"
echo "}"
