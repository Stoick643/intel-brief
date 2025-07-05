import praw
import logging
from datetime import datetime, timezone
from textblob import TextBlob
from app import db
from app.models import Source, RedditPost
from config import Config

logger = logging.getLogger(__name__)

class RedditCollector:
    def __init__(self):
        self.reddit = None
        self.subreddit_configs = [
            # AI & Technology
            {'name': 'MachineLearning', 'category': 'ai', 'limit': 10},
            {'name': 'artificial', 'category': 'ai', 'limit': 10},
            {'name': 'ArtificialIntelligence', 'category': 'ai', 'limit': 10},
            {'name': 'deeplearning', 'category': 'ai', 'limit': 10},
            {'name': 'ChatGPT', 'category': 'ai', 'limit': 10},
            
            # Science
            {'name': 'science', 'category': 'science', 'limit': 15},
            {'name': 'EverythingScience', 'category': 'science', 'limit': 10},
            {'name': 'biology', 'category': 'science', 'limit': 8},
            {'name': 'Physics', 'category': 'science', 'limit': 8},
            {'name': 'space', 'category': 'science', 'limit': 10},
            
            # International Relations
            {'name': 'worldnews', 'category': 'international', 'limit': 20},
            {'name': 'geopolitics', 'category': 'international', 'limit': 15},
            {'name': 'InternationalNews', 'category': 'international', 'limit': 10},
            {'name': 'foreignpolicy', 'category': 'international', 'limit': 8}
        ]
        
        # Initialize Reddit API
        self._init_reddit()
    
    def _init_reddit(self):
        """Initialize Reddit API client"""
        try:
            if not Config.REDDIT_CLIENT_ID or not Config.REDDIT_CLIENT_SECRET:
                logger.warning("Reddit API credentials not configured")
                return False
            
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            
            # Test connection
            self.reddit.auth.limits
            logger.info("Reddit API connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            return False
    
    def collect_all_subreddits(self):
        """Collect posts from all configured subreddits"""
        if not self.reddit:
            logger.error("Reddit API not initialized")
            return 0
        
        total_new_posts = 0
        
        for subreddit_config in self.subreddit_configs:
            try:
                new_posts = self.collect_subreddit(subreddit_config)
                total_new_posts += new_posts
                logger.info(f"Collected {new_posts} new posts from r/{subreddit_config['name']}")
            except Exception as e:
                logger.error(f"Error collecting from r/{subreddit_config['name']}: {str(e)}")
        
        return total_new_posts
    
    def collect_subreddit(self, subreddit_config):
        """Collect posts from a single subreddit"""
        source = self._get_or_create_source(subreddit_config)
        
        try:
            subreddit = self.reddit.subreddit(subreddit_config['name'])
            new_posts_count = 0
            
            # Get hot posts from subreddit
            for submission in subreddit.hot(limit=subreddit_config['limit']):
                try:
                    # Check if post already exists
                    existing_post = RedditPost.query.filter_by(reddit_id=submission.id).first()
                    if existing_post:
                        continue
                    
                    # Create new Reddit post
                    reddit_post = self._create_post_from_submission(submission, source, subreddit_config['category'])
                    if reddit_post:
                        db.session.add(reddit_post)
                        new_posts_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing post from r/{subreddit_config['name']}: {str(e)}")
                    continue
            
            # Update source statistics
            source.last_collected = datetime.utcnow()
            source.collection_count += 1
            
            db.session.commit()
            return new_posts_count
            
        except Exception as e:
            source.error_count += 1
            db.session.commit()
            logger.error(f"Error collecting subreddit r/{subreddit_config['name']}: {str(e)}")
            raise
    
    def _get_or_create_source(self, subreddit_config):
        """Get existing source or create new one"""
        subreddit_url = f"https://www.reddit.com/r/{subreddit_config['name']}"
        source = Source.query.filter_by(
            url=subreddit_url,
            source_type='reddit'
        ).first()
        
        if not source:
            source = Source(
                name=f"r/{subreddit_config['name']}",
                url=subreddit_url,
                source_type='reddit',
                category=subreddit_config['category']
            )
            db.session.add(source)
            db.session.commit()
        
        return source
    
    def _create_post_from_submission(self, submission, source, category):
        """Create RedditPost object from Reddit submission"""
        try:
            # Extract basic information
            title = submission.title
            reddit_id = submission.id
            url = submission.url if submission.url != submission.permalink else f"https://www.reddit.com{submission.permalink}"
            author = str(submission.author) if submission.author else "[deleted]"
            subreddit = submission.subreddit.display_name
            score = submission.score
            num_comments = submission.num_comments
            
            # Extract content
            content = ""
            if hasattr(submission, 'selftext') and submission.selftext:
                content = submission.selftext
            
            # Convert created_utc to datetime
            created_utc = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            
            # Basic sentiment analysis
            sentiment_score = None
            text_for_sentiment = f"{title} {content}"
            if text_for_sentiment.strip():
                try:
                    blob = TextBlob(text_for_sentiment)
                    sentiment_score = blob.sentiment.polarity
                except:
                    pass
            
            # Create Reddit post
            reddit_post = RedditPost(
                reddit_id=reddit_id,
                title=title,
                url=url,
                content=content,
                author=author,
                subreddit=subreddit,
                score=score,
                num_comments=num_comments,
                created_utc=created_utc,
                category=category,
                sentiment_score=sentiment_score,
                source_id=source.id
            )
            
            return reddit_post
            
        except Exception as e:
            logger.error(f"Error creating Reddit post from submission: {str(e)}")
            return None
    
    def get_subreddit_health(self):
        """Get health status of all Reddit sources"""
        sources = Source.query.filter_by(source_type='reddit').all()
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
                'health': 'good' if source.error_count == 0 else 'warning' if source.error_count < 5 else 'error',
                'total_posts': RedditPost.query.filter_by(source_id=source.id).count()
            }
            health_status.append(status)
        
        return health_status

# Scheduler job function
def scheduled_reddit_collection():
    """Function to be called by the scheduler"""
    try:
        collector = RedditCollector()
        if not collector.reddit:
            logger.warning("Reddit collection skipped - API not configured")
            return 0
            
        new_posts = collector.collect_all_subreddits()
        logger.info(f"Scheduled Reddit collection completed: {new_posts} new posts")
        return new_posts
    except Exception as e:
        logger.error(f"Scheduled Reddit collection failed: {str(e)}")
        return 0