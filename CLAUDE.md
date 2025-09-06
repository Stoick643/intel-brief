# Intelligence Briefing System - Claude Code Guide

A comprehensive Flask-based intelligence briefing system that collects and analyzes news from multiple sources including RSS feeds, Reddit, and Google Trends, with AI-powered analysis capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (tested with 3.13)
- Git
- Virtual environment support

### Get Running in 5 Minutes

```bash
# Clone and enter project
cd C:\projects\Claude\intel-brief

# Activate virtual environment
source venv/Scripts/activate  # Git Bash
# OR
venv\Scripts\activate         # Command Prompt

# Install dependencies (if needed)
pip install -r requirements.txt

# Run the application
py app.py
```

**Access:** http://localhost:5000

## 📋 Development Commands

### Essential Commands
```bash
# Activate virtual environment
source venv/Scripts/activate

# Run the application
py app.py

# Database migrations
flask db migrate -m "Description"
flask db upgrade

# Manual data collection
python -c "from app import create_app; from app.services.rss_collector import scheduled_rss_collection; app = create_app(); app.app_context().push(); print(f'Collected {scheduled_rss_collection()} articles')"
```

### Testing RSS Feeds
```bash
# Test individual components
python -c "
from app import create_app
from app.services.rss_collector import RSSCollector
app = create_app()
with app.app_context():
    collector = RSSCollector()
    articles = collector.collect_all_feeds()
    print(f'Collected {articles} new articles')
"
```

### Database Operations
```bash
# Check article counts
python -c "
from app import create_app, db
from app.models import Article
app = create_app()
with app.app_context():
    total = Article.query.count()
    ai = Article.query.filter_by(category='ai').count()
    science = Article.query.filter_by(category='science').count()
    intl = Article.query.filter_by(category='international').count()
    print(f'Total: {total}, AI: {ai}, Science: {science}, International: {intl}')
"
```

## 🏗️ Architecture Overview

### Core Components

1. **RSS Collector** (`app/services/rss_collector.py`)
   - Collects articles from configured RSS feeds
   - Filters articles by publication date (2025+ only)
   - Prevents duplicate articles by URL

2. **Reddit Collector** (`app/services/reddit_collector.py`)
   - Monitors relevant subreddits for posts
   - Requires Reddit API credentials in .env

3. **Trends Collector** (`app/services/trends_collector.py`)
   - Monitors Google Trends for keywords
   - Tracks trending topics by category

4. **AI Pipeline** (`app/services/ai_pipeline.py`)
   - Processes articles with AI agents
   - Uses DeepSeek and Claude APIs
   - Generates summaries and sentiment analysis

### Data Flow
```
RSS Feeds → RSS Collector → Database (Articles)
Reddit → Reddit Collector → Database (RedditPosts)  
Google Trends → Trends Collector → Database (Trends)
Database → AI Pipeline → Enhanced Articles
Database → Web Dashboard → User
```

## 💾 Database Models

### Key Tables
- **Articles** - RSS feed articles with AI analysis
- **RedditPosts** - Reddit submissions with metadata  
- **Trends** - Google Trends data points
- **Sources** - Configured data sources
- **AgentAnalysis** - AI processing results

### Database Location
- **Development:** `instance/intelligence_brief.db` (SQLite)
- **View with:** DBeaver, SQLite Browser, or VS Code extensions

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required for AI processing
DEEPSEEK_API_KEY=your-deepseek-key
ANTHROPIC_API_KEY=your-anthropic-key

# Required for Reddit
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret

# Article filtering
MINIMUM_ARTICLE_DATE=2025-01-01

# Collection intervals (minutes)
RSS_COLLECTION_INTERVAL=30
REDDIT_COLLECTION_INTERVAL=60
TRENDS_COLLECTION_INTERVAL=120

# AI processing limits
MAX_ARTICLES_PER_BATCH=50
AI_RETRY_COUNT=3
AI_TIMEOUT=30
```

### RSS Feed Sources (config.py)
Currently configured sources:
- **AI:** TechCrunch AI, Simon Willison, Ars Technica, MIT Tech Review, AI News
- **Science:** Nature News, Science Daily
- **International:** Foreign Affairs, Council on Foreign Relations

## 🔧 Troubleshooting

### Common Issues

#### "No Reddit posts collected"
- **Cause:** Missing Reddit API credentials
- **Fix:** Add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` to .env
- **Get Keys:** https://www.reddit.com/prefs/apps

#### Old articles reappearing
- **Cause:** RSS feeds contain old articles
- **Fix:** Date filter already implemented (2025+ only)
- **Verify:** Check `MINIMUM_ARTICLE_DATE` in config

#### RSS feeds returning 0 articles
- **Cause:** Feed URL changed or broken
- **Fix:** Update URL in `config.py` RSS_FEEDS list
- **Test:** Use feed validator or browser to check URL

#### Virtual environment issues
```bash
# Windows (Git Bash)
source venv/Scripts/activate

# Windows (Command Prompt)
venv\Scripts\activate

# Verify activation - should show (venv) in prompt
```

### Database Issues

#### Reset database
```bash
# Backup first
cp instance/intelligence_brief.db instance/backup.db

# Reset migrations
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

#### Clean up old articles
```bash
python -c "
from app import create_app, db
from app.models import Article
from datetime import datetime
from config import Config
app = create_app()
with app.app_context():
    cutoff = datetime.strptime(Config.MINIMUM_ARTICLE_DATE, '%Y-%m-%d')
    old_count = Article.query.filter(Article.published_date < cutoff).count()
    print(f'Found {old_count} old articles')
    if old_count > 0:
        Article.query.filter(Article.published_date < cutoff).delete()
        db.session.commit()
        print('Deleted old articles')
"
```

## 🧪 Testing

### Manual Testing
```bash
# Test RSS collection
python -c "from app import create_app; from app.services.rss_collector import RSSCollector; app = create_app(); app.app_context().push(); print('New articles:', RSSCollector().collect_all_feeds())"

# Test Reddit collection (if configured)
python -c "from app import create_app; from app.services.reddit_collector import scheduled_reddit_collection; app = create_app(); app.app_context().push(); print('New posts:', scheduled_reddit_collection())"

# Check dashboard data
curl http://localhost:5000/api/stats
```

### Verify System Health
- Dashboard loads: http://localhost:5000
- Articles display by category
- Sources show recent collection times
- No error logs in console

## 🌐 API Endpoints

### Public Endpoints
- `GET /` - Main dashboard
- `GET /ai` - AI news category
- `GET /science` - Science news category  
- `GET /international` - International news category
- `GET /article/<id>` - Article details

### Health & Monitoring
- `GET /health/check` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /api/stats` - System statistics

### Data Collection (Internal)
- `POST /api/collect-rss` - Trigger RSS collection
- `POST /api/collect-reddit` - Trigger Reddit collection
- `POST /api/collect-trends` - Trigger trends collection

## 🚀 Deployment Notes

### Local Development
- Uses SQLite database
- File-based logging
- Development server (Flask built-in)

### Production Considerations
- Switch to PostgreSQL for database
- Use Gunicorn for WSGI server
- Configure proper logging
- Set up monitoring and alerts
- Secure API keys in environment variables

### Environment Setup
- Python 3.11+ recommended
- Virtual environment required
- Git for version control
- Consider Docker for containerization

## 📝 Development Workflow

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes
3. Test locally
4. Update documentation if needed
5. Commit with descriptive message
6. Push and create pull request

### Updating RSS Feeds
1. Test new feed URL manually
2. Update `config.py` RSS_FEEDS list
3. Run test collection
4. Commit changes

### Database Schema Changes
1. Modify models in `app/models.py`
2. Create migration: `flask db migrate -m "Description"`
3. Apply migration: `flask db upgrade`
4. Test with sample data
5. Commit migration files

## 🔒 Security Notes

- Never commit API keys to git
- Use environment variables for secrets
- Keep .env file in .gitignore
- Regularly update dependencies
- Monitor for suspicious activity in logs

## 📚 Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/
- **Reddit API:** https://www.reddit.com/dev/api/
- **Google Trends API:** pytrends documentation
- **DeepSeek API:** DeepSeek platform docs
- **Anthropic Claude:** https://docs.anthropic.com/

---

**Intelligence Briefing System** - Your automated intelligence gathering and analysis platform.

*Last updated: September 2025*