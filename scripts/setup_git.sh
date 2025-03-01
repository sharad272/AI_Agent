#!/bin/bash

# Check if GPG key exists
gpg --list-secret-keys --keyid-format LONG

# Configure Git to use GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_GPG_KEY_ID

# Test the configuration
echo "Git signing configuration complete!"
echo "Try committing with: git commit -S -m 'your message'"
