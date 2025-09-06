import feedparser
import requests
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import logging
from textblob import TextBlob
from app import db
from app.models import Source, Article
from config import Config

logger = logging.getLogger(__name__)

class RSSCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def collect_all_feeds(self):
        """Collect articles from all configured RSS feeds"""
        total_new_articles = 0
        
        for feed_config in Config.RSS_FEEDS:
            try:
                new_articles = self.collect_feed(feed_config)
                total_new_articles += new_articles
                logger.info(f"Collected {new_articles} new articles from {feed_config['name']}")
            except Exception as e:
                logger.error(f"Error collecting from {feed_config['name']}: {str(e)}")
        
        return total_new_articles
    
    def collect_feed(self, feed_config):
        """Collect articles from a single RSS feed"""
        source = self._get_or_create_source(feed_config)
        
        try:
            # Parse the RSS feed
            feed = feedparser.parse(feed_config['url'])
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_config['name']}: {feed.bozo_exception}")
            
            new_articles_count = 0
            
            for entry in feed.entries:
                try:
                    # Check if article already exists
                    existing_article = Article.query.filter_by(url=entry.link).first()
                    if existing_article:
                        continue
                    
                    # Create new article
                    article = self._create_article_from_entry(entry, source, feed_config['category'])
                    if article:
                        # Check if article is too old
                        minimum_date = datetime.strptime(Config.MINIMUM_ARTICLE_DATE, '%Y-%m-%d')
                        if article.published_date and article.published_date < minimum_date:
                            logger.debug(f"Skipping old article from {article.published_date}: {article.title[:50]}")
                            continue
                        
                        db.session.add(article)
                        new_articles_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing entry from {feed_config['name']}: {str(e)}")
                    continue
            
            # Update source statistics
            source.last_collected = datetime.utcnow()
            source.collection_count += 1
            
            db.session.commit()
            return new_articles_count
            
        except Exception as e:
            source.error_count += 1
            db.session.commit()
            logger.error(f"Error collecting feed {feed_config['name']}: {str(e)}")
            raise
    
    def _get_or_create_source(self, feed_config):
        """Get existing source or create new one"""
        source = Source.query.filter_by(
            url=feed_config['url'],
            source_type='rss'
        ).first()
        
        if not source:
            source = Source(
                name=feed_config['name'],
                url=feed_config['url'],
                source_type='rss',
                category=feed_config['category']
            )
            db.session.add(source)
            db.session.commit()
        
        return source
    
    def _create_article_from_entry(self, entry, source, category):
        """Create Article object from RSS entry"""
        try:
            # Extract basic information
            title = entry.title if hasattr(entry, 'title') else 'No Title'
            url = entry.link if hasattr(entry, 'link') else None
            
            if not url:
                return None
            
            # Extract content
            content = self._extract_content(entry)
            summary = self._extract_summary(entry)
            
            # Extract author
            author = None
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                author = entry.authors[0] if isinstance(entry.authors, list) else entry.authors
            
            # Extract published date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6])
            
            # Basic sentiment analysis
            sentiment_score = None
            if content:
                try:
                    blob = TextBlob(content)
                    sentiment_score = blob.sentiment.polarity
                except:
                    pass
            
            # Create article
            article = Article(
                title=title,
                url=url,
                content=content,
                summary=summary,
                author=author,
                published_date=published_date,
                category=category,
                sentiment_score=sentiment_score,
                source_id=source.id
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Error creating article from entry: {str(e)}")
            return None
    
    def _extract_content(self, entry):
        """Extract content from RSS entry"""
        content = ""
        
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Clean HTML tags (basic cleaning)
        if content:
            import re
            content = re.sub(r'<[^>]+>', '', content)
            content = content.strip()
        
        return content
    
    def _extract_summary(self, entry):
        """Extract summary from RSS entry"""
        if hasattr(entry, 'summary'):
            summary = entry.summary
            # Clean HTML tags
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            return summary.strip()
        return None
    
    def get_feed_health(self):
        """Get health status of all RSS feeds"""
        sources = Source.query.filter_by(source_type='rss').all()
        health_status = []
        
        for source in sources:
            status = {
                'name': source.name,
                'url': source.url,
                'category': source.category,
                'is_active': source.is_active,
                'last_collected': source.last_collected,
                'collection_count': source.collection_count,
                'error_count': source.error_count,
                'health': 'good' if source.error_count == 0 else 'warning' if source.error_count < 5 else 'error'
            }
            health_status.append(status)
        
        return health_status

# Scheduler job function
def scheduled_rss_collection():
    """Function to be called by the scheduler"""
    try:
        collector = RSSCollector()
        new_articles = collector.collect_all_feeds()
        logger.info(f"Scheduled RSS collection completed: {new_articles} new articles")
        return new_articles
    except Exception as e:
        logger.error(f"Scheduled RSS collection failed: {str(e)}")
        return 0