#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Run the app with Gunicorn (Azure uses this)
gunicorn --bind=0.0.0.0:8000 --workers=4 app:app