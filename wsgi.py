#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
This creates the Flask app instance for Gunicorn.
"""

from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    app.run()