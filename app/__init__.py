from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import os

db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        # Default configuration
        from config import Config
        app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Set up logging
    from app.utils.logging_config import setup_logging
    setup_logging(app)
    
    # Initialize security
    from app.utils.security import init_security
    init_security(app)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Register monitoring blueprint
    from app.utils.monitoring import monitoring_bp
    app.register_blueprint(monitoring_bp)
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
    
    return app

from app import models