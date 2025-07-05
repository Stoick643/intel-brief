# Intelligence Briefing System

A Flask-based intelligence briefing system that collects AI/science/international relations news from RSS feeds, Reddit, and Google Trends, with AI-powered analysis and summarization.

## Features

### Core Features (Session 1 - Current)
- ✅ **RSS Feed Collection**: Automated collection from AI, science, and international relations sources
- ✅ **Web Dashboard**: Clean Bootstrap-based interface for browsing articles
- ✅ **Content Quality Scoring**: Basic heuristic-based quality assessment
- ✅ **Sentiment Analysis**: Basic sentiment detection using TextBlob
- ✅ **Source Management**: Health monitoring and statistics for RSS sources
- ✅ **AI Agent Foundation**: Framework for AI-powered content analysis

### Planned Features (Future Sessions)
- 🔄 **Reddit Integration**: Collection from relevant subreddits (Session 3)
- 🔄 **Google Trends**: Trend detection and analysis (Session 3)
- 🔄 **DeepSeek API**: Bulk content processing and quality scoring (Session 4)
- 🔄 **Claude API**: Complex analysis and trend synthesis (Session 4)
- 🔄 **Alert System**: Intelligent alerting based on content and trends (Session 4)
- 🔄 **Production Deployment**: Docker, monitoring, and scaling (Session 5)

## Technology Stack

- **Backend**: Python 3.8+, Flask, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Jinja2 templates, Bootstrap 5, JavaScript
- **Task Scheduling**: APScheduler
- **RSS Parsing**: feedparser
- **NLP**: TextBlob, future AI API integration
- **Testing**: pytest

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd /home/dmulej/intel-brief
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**:
   ```bash
   flask init-db
   flask seed-db
   ```

6. **Run the application**:
   ```bash
   flask run
   ```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///intelligence_brief.db
FLASK_ENV=development

# AI API Keys (for future sessions)
DEEPSEEK_API_KEY=your-deepseek-api-key
CLAUDE_API_KEY=your-claude-api-key
ENABLE_AI_AGENTS=true

# Reddit API (for Session 3)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=IntelligenceBriefing/1.0

# Collection Intervals (in minutes)
RSS_COLLECTION_INTERVAL=30
REDDIT_COLLECTION_INTERVAL=60
TRENDS_COLLECTION_INTERVAL=120
```

### RSS Sources

The system is pre-configured with these RSS sources:

**AI Sources**:
- Anthropic Blog
- Simon Willison's Blog
- OpenAI Blog
- MIT Technology Review AI

**Science Sources**:
- Nature News
- Science Daily

**International Relations**:
- Foreign Affairs
- Council on Foreign Relations

Sources are automatically added to the database when the RSS collector runs.

## Usage

### Web Interface

1. **Dashboard** (`/`): Overview of recent articles, statistics, and alerts
2. **AI Section** (`/ai`): AI and technology news
3. **Science Section** (`/science`): Science and research news
4. **International Section** (`/international`): International relations news
5. **Sources** (`/sources`): RSS source health and statistics
6. **AI Agents** (`/ai-agents`): AI processing status and performance

### CLI Commands

```bash
# Initialize database
flask init-db

# Seed with sample data
flask seed-db

# Manually collect RSS feeds
flask collect-rss
```

### API Endpoints

- `POST /api/collect-rss`: Manually trigger RSS collection
- `POST /api/process-ai/<article_id>`: Process article with AI agents
- `POST /api/feedback`: Submit user feedback
- `POST /api/mark-alert-read/<alert_id>`: Mark alert as read
- `GET /api/stats`: Get system statistics

## Data Models

### Core Models
- **Source**: RSS feeds, Reddit sources, etc.
- **Article**: News articles from RSS feeds
- **RedditPost**: Posts from Reddit (Session 3)
- **Trend**: Google Trends data (Session 3)
- **Alert**: System alerts and notifications

### AI Integration Models
- **AgentAnalysis**: Results from AI agent processing
- **AgentPerformance**: Performance metrics for AI agents
- **UserFeedback**: User ratings and feedback

## AI Agent System

The system includes a flexible AI agent framework:

### Agent Types
1. **ContentQualityAgent**: Scores article quality and relevance
2. **SummaryAgent**: Generates article summaries
3. **TrendSynthesisAgent**: Analyzes trends across multiple sources
4. **AlertPrioritizationAgent**: Prioritizes alerts and notifications

### Fallback Mechanisms
- All agents work without AI APIs using heuristic methods
- Graceful degradation when APIs are unavailable
- Retry logic with exponential backoff

## Development

### Project Structure
```
intel-brief/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes.py            # Web routes
│   ├── services/
│   │   ├── rss_collector.py # RSS collection service
│   │   └── ai_agents.py     # AI agent framework
│   └── templates/           # HTML templates
├── config.py                # Configuration
├── app.py                   # Main application
├── requirements.txt         # Dependencies
└── README.md               # This file
```

### Running Tests
```bash
pytest
```

### Code Style
```bash
black .
flake8 .
```

## Session Plan

### Session 1: Flask Foundation + RSS Collection ✅
- [x] Basic Flask app structure
- [x] SQLAlchemy models with AI fields
- [x] RSS collection service
- [x] Web dashboard with Bootstrap
- [x] AI agent framework foundation

### Session 2: Web Dashboard Functional (Next)
- [ ] Enhanced UI/UX
- [ ] Article detail pages
- [ ] User feedback system
- [ ] Search and filtering
- [ ] Performance optimizations

### Session 3: Reddit + Google Trends Integration
- [ ] Reddit API integration
- [ ] Google Trends collection
- [ ] Cross-source correlation
- [ ] Enhanced trending detection

### Session 4: Complete AI Agent Integration
- [ ] DeepSeek API integration
- [ ] Claude API integration
- [ ] Advanced content analysis
- [ ] Intelligent alerting system

### Session 5: Production Polish + Deployment
- [ ] Docker containerization
- [ ] Production database setup
- [ ] Monitoring and logging
- [ ] Performance optimization
- [ ] Security hardening

## Troubleshooting

### Common Issues

1. **RSS Collection Fails**:
   - Check internet connection
   - Verify RSS feed URLs in `config.py`
   - Check source status in `/sources`

2. **Database Errors**:
   - Run `flask init-db` to recreate tables
   - Check database file permissions

3. **AI Agents Not Working**:
   - Verify `ENABLE_AI_AGENTS=true` in `.env`
   - Check API keys (when configured)
   - Agents fall back to heuristic methods

### Logging
Check the Flask development server output for error messages and collection status.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is for educational and research purposes.

## Session 1 Status: ✅ Complete

The Flask foundation and RSS collection system is now fully functional. The system can:
- Collect articles from configured RSS feeds
- Display articles in a clean web interface
- Score article quality using heuristic methods
- Process content with AI agent framework (fallback mode)
- Monitor source health and performance
- Accept user feedback

Ready for Session 2: Enhanced Dashboard Functionality!