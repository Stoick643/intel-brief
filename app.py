from app import create_app, db, scheduler
from app.services.rss_collector import scheduled_rss_collection
from config import Config

app = create_app()

def setup_scheduler():
    """Setup scheduled tasks"""
    if not scheduler.running:
        scheduler.add_job(
            func=scheduled_rss_collection,
            trigger="interval",
            minutes=Config.RSS_COLLECTION_INTERVAL,
            id='rss_collection',
            name='RSS Collection Job',
            replace_existing=True
        )
        scheduler.start()

# Setup scheduler on app context
with app.app_context():
    setup_scheduler()

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")

@app.cli.command()
def seed_db():
    """Seed the database with sample data."""
    from app.models import Source, Alert
    from datetime import datetime
    
    # Create sample sources (will be created automatically by RSS collector)
    # But we can create a sample alert
    sample_alert = Alert(
        title="System Started",
        message="Intelligence Briefing System has been initialized and is collecting data.",
        alert_type="system_info",
        priority="low",
        category="system"
    )
    
    db.session.add(sample_alert)
    db.session.commit()
    print("Database seeded with sample data!")

@app.cli.command()
def collect_rss():
    """Manually trigger RSS collection."""
    new_articles = scheduled_rss_collection()
    print(f"RSS collection completed: {new_articles} new articles collected")

if __name__ == '__main__':
    app.run(debug=True)