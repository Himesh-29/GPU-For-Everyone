#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies using uv
pip install uv
uv pip install --system -r requirements.txt

# Create custom migrations directory if it doesn't exist
mkdir -p backend/custom_migrations/sites
touch backend/custom_migrations/__init__.py
touch backend/custom_migrations/sites/__init__.py

# Collect static files
python backend/manage.py collectstatic --no-input

# Run migrations
python backend/manage.py migrate
