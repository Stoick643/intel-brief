# Intelligence Briefing System

A comprehensive Flask-based intelligence briefing system that collects and analyzes news from multiple sources including RSS feeds, Reddit, and Google Trends, with AI-powered analysis capabilities.

## 🚀 Features

- **Multi-Source Data Collection**
  - RSS feed aggregation from AI, science, and international news sources
  - Reddit post collection from relevant subreddits
  - Google Trends monitoring for trending topics
  - Automated collection scheduling with APScheduler

- **AI-Powered Analysis**
  - Content quality scoring with DeepSeek and Claude APIs
  - Article summarization and key insights extraction
  - Trend synthesis and pattern recognition
  - Alert prioritization and threat assessment

- **Web Dashboard**
  - Bootstrap 5 responsive interface
  - Real-time statistics and visualizations
  - Article categorization and search
  - Source health monitoring

- **Production-Ready**
  - Comprehensive logging and monitoring
  - Security hardening and rate limiting
  - Docker containerization
  - Database migrations and backups
  - Performance optimization with caching

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🏃 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for production deployment)
- PostgreSQL (for production) or SQLite (for development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd intel-brief
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   python app.py seed-db
   ```

6. **Run the application**
   ```bash
   python app.py
   # Or: flask run --port 5000
   ```

7. **Access the application**
   - Main dashboard: http://localhost:5000
   - Health check: http://localhost:5000/health/check

## 🔧 Installation

### System Requirements

- **Hardware**: 2+ CPU cores, 4GB+ RAM, 10GB+ storage
- **Software**: Python 3.11+, PostgreSQL 13+, Redis 6+ (optional)
- **Network**: Internet access for data collection

### Detailed Installation Steps

1. **System Dependencies** (Ubuntu/Debian)
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev
   sudo apt install postgresql postgresql-contrib redis-server
   sudo apt install build-essential libpq-dev
   ```

2. **Database Setup**
   ```bash
   sudo -u postgres createuser --interactive intel_brief
   sudo -u postgres createdb intel_brief_db -O intel_brief
   ```

3. **Python Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

### Environment Variables

The system uses environment variables for configuration. Copy `.env.example` to `.env` and modify:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production

# Database Configuration
DATABASE_URL=sqlite:///intelligence_brief.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# AI API Keys (Optional - system works without them)
DEEPSEEK_API_KEY=your-deepseek-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Reddit API Configuration (Optional)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=IntelligenceBriefing/1.0

# Data Collection Intervals (minutes)
RSS_COLLECTION_INTERVAL=30
REDDIT_COLLECTION_INTERVAL=60
TRENDS_COLLECTION_INTERVAL=120

# AI Processing Configuration
ENABLE_AI_AGENTS=true
MAX_ARTICLES_PER_BATCH=50
AI_RETRY_COUNT=3
AI_TIMEOUT=30

# Security Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_TO_FILE=true

# Monitoring Configuration
HEALTH_CHECK_ENABLED=true
METRICS_ENABLED=true
```

### RSS Feed Sources

The system comes pre-configured with high-quality sources:

**AI & Technology:**
- Anthropic Blog
- Simon Willison's Blog
- OpenAI Blog
- MIT Technology Review AI

**Science:**
- Nature News
- Science Daily

**International Relations:**
- Foreign Affairs
- Council on Foreign Relations

### Reddit Subreddits

Monitored subreddits include:
- AI/ML: MachineLearning, artificial, singularity, LocalLLaMA
- Science: science, technology, Futurology, datascience
- International: worldnews, geopolitics, europe, UkrainianConflict

### Google Trends Keywords

**AI/Technology:**
- artificial intelligence, machine learning, ChatGPT, GPT-4, neural networks

**Science:**
- climate change, quantum computing, biotechnology, space exploration, renewable energy

**International:**
- NATO, European Union, China trade, cybersecurity, sanctions

## 🛠️ Development

### Development Commands

```bash
# Database operations
flask db init                    # Initialize migration repository
flask db migrate -m "message"    # Create new migration
flask db upgrade                 # Apply migrations
flask db downgrade              # Rollback migrations

# Application commands
python app.py seed-db           # Seed database with initial data
python app.py collect-rss       # Manual RSS collection
python app.py collect-reddit    # Manual Reddit collection
python app.py collect-trends    # Manual Google Trends collection
python app.py process-ai        # Manual AI processing

# Testing
pytest                          # Run all tests
pytest tests/test_app.py        # Run specific test file
pytest --cov=app              # Run with coverage
```

### Project Structure

```
intel-brief/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── routes.py             # Web routes and API endpoints
│   ├── services/             # Business logic
│   │   ├── rss_collector.py  # RSS feed collection
│   │   ├── reddit_collector.py # Reddit API integration
│   │   ├── trends_collector.py # Google Trends collection
│   │   ├── ai_agents.py      # AI processing agents
│   │   └── ai_pipeline.py    # AI processing pipeline
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html         # Base template
│   │   ├── dashboard.html    # Main dashboard
│   │   ├── category.html     # Category pages
│   │   └── article_detail.html # Article detail
│   └── utils/                # Utilities
│       ├── logging_config.py # Logging configuration
│       ├── monitoring.py     # Health checks and metrics
│       ├── security.py       # Security middleware
│       └── cache.py          # Caching utilities
├── config/
│   └── production.py         # Production configuration
├── migrations/               # Database migrations
├── tests/                   # Test suite
├── logs/                    # Application logs
├── app.py                   # Application entry point
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── deploy.sh               # Deployment script
└── README.md               # This file
```

### Adding New Features

1. **New Data Source**
   - Create collector in `app/services/`
   - Add database model in `app/models.py`
   - Create migration: `flask db migrate`
   - Add route in `app/routes.py`
   - Update dashboard template

2. **New AI Agent**
   - Add agent class in `app/services/ai_agents.py`
   - Update pipeline in `app/services/ai_pipeline.py`
   - Add performance tracking

3. **New API Endpoint**
   - Add route in `app/routes.py`
   - Add error handling and logging
   - Apply security decorators
   - Write tests

## 🚀 Production Deployment

### Docker Deployment (Recommended)

1. **Prepare environment**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd intel-brief
   
   # Copy and configure environment
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy with script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh production
   ```

3. **Manual Docker deployment**
   ```bash
   # Build and start services
   docker-compose up -d
   
   # Run migrations
   docker-compose exec app flask db upgrade
   
   # Seed database
   docker-compose exec app python app.py seed-db
   
   # Check health
   curl http://localhost:5000/health/check
   ```

### VPS Deployment

1. **Server setup**
   ```bash
   # Install dependencies
   sudo apt update
   sudo apt install python3.11 python3.11-venv nginx postgresql redis-server
   
   # Create application user
   sudo useradd -m -s /bin/bash intel-brief
   sudo su - intel-brief
   ```

2. **Application setup**
   ```bash
   # Clone and setup
   git clone <repository-url> app
   cd app
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with production settings
   
   # Setup database
   flask db upgrade
   python app.py seed-db
   ```

3. **Service configuration**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/intel-brief.service
   ```

   ```ini
   [Unit]
   Description=Intelligence Briefing System
   After=network.target
   
   [Service]
   Type=exec
   User=intel-brief
   WorkingDirectory=/home/intel-brief/app
   Environment=PATH=/home/intel-brief/app/venv/bin
   ExecStart=/home/intel-brief/app/venv/bin/gunicorn --bind unix:/home/intel-brief/app/intel-brief.sock --workers 4 app:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Nginx configuration**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://unix:/home/intel-brief/app/intel-brief.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Monitoring and Maintenance

1. **Health Monitoring**
   ```bash
   # Check application health
   curl http://localhost:5000/health/detailed
   
   # View logs
   docker-compose logs -f app
   # Or: sudo journalctl -u intel-brief -f
   ```

2. **Database Backup**
   ```bash
   # Docker deployment
   docker-compose exec db pg_dump -U intel_brief intel_brief_db > backup_$(date +%Y%m%d).sql
   
   # VPS deployment
   pg_dump -U intel_brief intel_brief_db > backup_$(date +%Y%m%d).sql
   ```

3. **Performance Monitoring**
   - Prometheus metrics: `http://localhost:5000/health/metrics`
   - System metrics via monitoring endpoint
   - Log analysis in `logs/` directory

## 📚 API Documentation

### Health Endpoints

- `GET /health/check` - Basic health check
- `GET /health/detailed` - Detailed health with metrics
- `GET /health/metrics` - Prometheus-compatible metrics

### Data Collection Endpoints

- `POST /api/collect-rss` - Trigger RSS collection
- `POST /api/collect-reddit` - Trigger Reddit collection
- `POST /api/collect-trends` - Trigger Google Trends collection
- `POST /api/process-ai-pipeline` - Trigger AI processing

### Information Endpoints

- `GET /api/stats` - Application statistics
- `GET /` - Main dashboard
- `GET /ai` - AI news section
- `GET /science` - Science news section
- `GET /international` - International relations section
- `GET /article/<id>` - Article detail page

### Management Endpoints

- `POST /api/feedback` - Submit user feedback
- `POST /api/mark-alert-read/<id>` - Mark alert as read

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_app.py          # Application tests
pytest tests/test_models.py       # Model tests
pytest tests/test_collectors.py   # Collector tests
```

### Test Categories

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Component interaction testing
3. **API Tests** - Endpoint functionality testing
4. **Model Tests** - Database model testing

### Writing Tests

```python
def test_new_feature(client, app):
    \"\"\"Test new feature functionality\"\"\"
    with app.app_context():
        # Test implementation
        response = client.get('/new-endpoint')
        assert response.status_code == 200
```

## 🔒 Security

### Security Features

- **Authentication & Authorization** - Session-based security
- **Input Validation** - SQL injection and XSS prevention
- **Rate Limiting** - API abuse protection
- **Security Headers** - CSRF, XSS, clickjacking protection
- **HTTPS Enforcement** - TLS/SSL in production
- **Content Security Policy** - Script injection prevention

### Security Configuration

```python
# Security settings in production.py
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
FORCE_HTTPS = True
RATE_LIMIT_ENABLED = True
```

### Security Best Practices

1. **Environment Variables** - Never commit secrets to code
2. **Regular Updates** - Keep dependencies updated
3. **Access Control** - Limit API access with keys
4. **Monitoring** - Log security events
5. **Backups** - Regular encrypted backups

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check database status
   docker-compose ps db
   # Or: sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U intel_brief -d intel_brief_db
   ```

2. **API Key Issues**
   ```bash
   # Check environment variables
   echo $ANTHROPIC_API_KEY
   
   # Test API connection
   curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/complete
   ```

3. **Collection Not Working**
   ```bash
   # Check logs
   docker-compose logs app | grep collector
   
   # Manual test
   docker-compose exec app python app.py collect-rss
   ```

4. **High Memory Usage**
   ```bash
   # Check system resources
   docker stats
   
   # Clear cache
   docker-compose exec app python -c "from app.utils.cache import cache; cache.clear()"
   ```

### Log Analysis

```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/error.log

# Collection logs
tail -f logs/collection.log

# AI processing logs
tail -f logs/ai_processing.log
```

### Performance Optimization

1. **Database Optimization**
   - Regular VACUUM and ANALYZE
   - Proper indexing
   - Connection pooling

2. **Caching Strategy**
   - Dashboard statistics caching
   - Article list caching
   - Source health caching

3. **Resource Monitoring**
   - CPU and memory usage
   - Database performance
   - API response times

## 🔄 Updates and Maintenance

### Update Process

1. **Backup Data**
   ```bash
   ./deploy.sh backup
   ```

2. **Pull Updates**
   ```bash
   git pull origin main
   ```

3. **Update Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   flask db upgrade
   ```

5. **Restart Services**
   ```bash
   docker-compose restart
   ```

### Maintenance Tasks

- **Daily**: Check logs and health status
- **Weekly**: Review system metrics and performance
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Full system backup and disaster recovery test

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document new features
- Update README for significant changes

## 📞 Support

For support and questions:

1. Check the [documentation](#table-of-contents)
2. Search existing [issues](../../issues)
3. Create a new [issue](../../issues/new) with details

---

**Intelligence Briefing System** - Keeping you informed with AI-powered intelligence gathering and analysis.