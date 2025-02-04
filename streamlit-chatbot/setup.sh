#!/bin/bash

# This script sets up the environment for the Streamlit chatbot project.

# Update package list and install Python3 and pip if not already installed
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Navigate to the src directory
cd src

# Install the required Python packages
pip3 install -r requirements.txt

# Inform the user that the setup is complete
echo "Setup complete. You can now run the Streamlit app using 'streamlit run app.py'."