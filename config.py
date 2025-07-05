import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///intelligence_brief.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # RSS Feed Configuration
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
    
    # AI Agent Configuration
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    ENABLE_AI_AGENTS = os.environ.get('ENABLE_AI_AGENTS', 'true').lower() == 'true'
    
    # Reddit Configuration
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'IntelligenceBriefing/1.0')
    
    # Collection intervals
    RSS_COLLECTION_INTERVAL = int(os.environ.get('RSS_COLLECTION_INTERVAL', '30'))  # minutes
    REDDIT_COLLECTION_INTERVAL = int(os.environ.get('REDDIT_COLLECTION_INTERVAL', '60'))  # minutes
    TRENDS_COLLECTION_INTERVAL = int(os.environ.get('TRENDS_COLLECTION_INTERVAL', '120'))  # minutes
    
    # AI processing limits
    MAX_ARTICLES_PER_BATCH = int(os.environ.get('MAX_ARTICLES_PER_BATCH', '50'))
    AI_RETRY_COUNT = int(os.environ.get('AI_RETRY_COUNT', '3'))
    AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '30'))  # seconds