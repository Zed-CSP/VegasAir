#!/bin/bash

# Add all changes
git add -A

# Create timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")

# Commit with timestamp
git commit -m "commit_${timestamp}"

# Push to remote
git push

echo "Changes committed and pushed with timestamp: ${timestamp}" 