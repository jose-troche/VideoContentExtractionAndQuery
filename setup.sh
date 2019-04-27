#!/usr/bin/env bash

# Sets up environment

# Prerequisites: Python3

python3 -m venv videoApp
. videoApp/bin/activate
pip install boto3

# Uncomment to deactivate python isolated environment
# deactivate
