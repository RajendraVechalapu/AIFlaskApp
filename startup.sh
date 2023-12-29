#!/bin/bash

# Create a new virtual environment
python -m venv rajenv

# Activate the virtual environment
source rajenv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt
