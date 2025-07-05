import os
from datetime import timedelta

class ProductionConfig:
    """Production configuration settings"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable must be set in production")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Flask Settings
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security Headers
    FORCE_HTTPS = True
    
    # AI Agent Configuration
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
    ENABLE_AI_AGENTS = os.environ.get('ENABLE_AI_AGENTS', 'true').lower() == 'true'
    
    # Reddit Configuration
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'IntelligenceBriefing/1.0')
    
    # Collection intervals (minutes)
    RSS_COLLECTION_INTERVAL = int(os.environ.get('RSS_COLLECTION_INTERVAL', '30'))
    REDDIT_COLLECTION_INTERVAL = int(os.environ.get('REDDIT_COLLECTION_INTERVAL', '60'))
    TRENDS_COLLECTION_INTERVAL = int(os.environ.get('TRENDS_COLLECTION_INTERVAL', '120'))
    
    # AI processing limits
    MAX_ARTICLES_PER_BATCH = int(os.environ.get('MAX_ARTICLES_PER_BATCH', '50'))
    AI_RETRY_COUNT = int(os.environ.get('AI_RETRY_COUNT', '3'))
    AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '30'))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'
    
    # Monitoring
    HEALTH_CHECK_ENABLED = os.environ.get('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
    METRICS_ENABLED = os.environ.get('METRICS_ENABLED', 'true').lower() == 'true'
    
    # Performance
    WORKERS = int(os.environ.get('WORKERS', '4'))
    MAX_CONNECTIONS = int(os.environ.get('MAX_CONNECTIONS', '1000'))
    
    # Security
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
    
    # RSS Feed Configuration (Production optimized)
    RSS_FEEDS = [
        {
            'name': 'Anthropic Blog',
            'url': 'https://www.anthropic.com/news/rss.xml',
            'category': 'ai'
        },
        {
            'name': 'Simon Willison',
            'url': 'https://simonwillison.net/atom/',
            'category': 'ai'
        },
        {
            'name': 'OpenAI Blog',
            'url': 'https://openai.com/blog/rss/',
            'category': 'ai'
        },
        {
            'name': 'MIT Technology Review AI',
            'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed/',
            'category': 'ai'
        },
        {
            'name': 'Nature News',
            'url': 'https://www.nature.com/nature.rss',
            'category': 'science'
        },
        {
            'name': 'Science Daily',
            'url': 'https://www.sciencedaily.com/rss/top/science.xml',
            'category': 'science'
        },
        {
            'name': 'Foreign Affairs',
            'url': 'https://www.foreignaffairs.com/rss.xml',
            'category': 'international'
        },
        {
            'name': 'Council on Foreign Relations',
            'url': 'https://www.cfr.org/rss-feeds/publications',
            'category': 'international'
        }
    ]