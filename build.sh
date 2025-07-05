#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create initial database tables (skip migrations for now)
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created!')
"