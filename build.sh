#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python -m flask db upgrade

# Create initial database tables if they don't exist
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables ensured!')
"