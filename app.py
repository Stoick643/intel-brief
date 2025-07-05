from app import create_app, db, scheduler
from app.services.rss_collector import scheduled_rss_collection
from app.services.reddit_collector import scheduled_reddit_collection
from app.services.trends_collector import scheduled_trends_collection
from app.services.ai_pipeline import scheduled_ai_processing
from config import Config

app = create_app()

def setup_scheduler():
    """Setup scheduled tasks"""
    if not scheduler.running:
        # RSS Collection Job
        scheduler.add_job(
            func=scheduled_rss_collection,
            trigger="interval",
            minutes=Config.RSS_COLLECTION_INTERVAL,
            id='rss_collection',
            name='RSS Collection Job',
            replace_existing=True
        )
        
        # Reddit Collection Job
        scheduler.add_job(
            func=scheduled_reddit_collection,
            trigger="interval",
            minutes=Config.REDDIT_COLLECTION_INTERVAL,
            id='reddit_collection',
            name='Reddit Collection Job',
            replace_existing=True
        )
        
        # Google Trends Collection Job
        scheduler.add_job(
            func=scheduled_trends_collection,
            trigger="interval",
            minutes=Config.TRENDS_COLLECTION_INTERVAL,
            id='trends_collection',
            name='Google Trends Collection Job',
            replace_existing=True
        )
        
        # AI Processing Job
        scheduler.add_job(
            func=scheduled_ai_processing,
            trigger="interval",
            minutes=30,  # Run AI processing every 30 minutes
            id='ai_processing',
            name='AI Processing Pipeline Job',
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

@app.cli.command()
def collect_reddit():
    """Manually trigger Reddit collection."""
    new_posts = scheduled_reddit_collection()
    print(f"Reddit collection completed: {new_posts} new posts collected")

@app.cli.command()
def collect_trends():
    """Manually trigger Google Trends collection."""
    new_trends = scheduled_trends_collection()
    print(f"Google Trends collection completed: {new_trends} new trend entries collected")

@app.cli.command()
def process_ai():
    """Manually trigger AI processing pipeline."""
    results = scheduled_ai_processing()
    print(f"AI processing completed:")
    print(f"  Articles processed: {results.get('articles_processed', 0)}")
    print(f"  Reddit posts processed: {results.get('reddit_posts_processed', 0)}")
    print(f"  Trend analyses created: {results.get('trend_analyses_created', 0)}")
    print(f"  Alerts prioritized: {results.get('alerts_prioritized', 0)}")

if __name__ == '__main__':
    app.run(debug=True)