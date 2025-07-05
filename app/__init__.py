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
    
    # Trigger initial data collection on startup (avoid cold start)
    def initial_data_collection():
        """Collect initial data when app starts"""
        import threading
        import time
        from app.utils.logging_config import get_logger
        
        logger = get_logger(__name__)
        
        def collect_data():
            # Wait a bit for app to fully initialize
            time.sleep(5)
            
            with app.app_context():
                try:
                    from app.services.rss_collector import scheduled_rss_collection
                    logger.info("Starting initial data collection...")
                    articles = scheduled_rss_collection()
                    logger.info(f"Initial collection completed: {articles} articles collected")
                except Exception as e:
                    logger.warning(f"Initial data collection failed: {e}")
        
        # Run in background thread so it doesn't block app startup
        thread = threading.Thread(target=collect_data, daemon=True)
        thread.start()
    
    # Only run initial collection in production/normal startup
    # Skip during testing or when running Flask CLI commands
    if not (app.config.get('TESTING') or os.environ.get('FLASK_RUN_FROM_CLI')):
        initial_data_collection()
    
    return app

from app import models