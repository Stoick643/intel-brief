import logging
from datetime import datetime, timedelta
from app import db
from app.models import Article, RedditPost, Trend, Alert, AgentAnalysis
from app.services.ai_agents import ContentQualityAgent, SummaryAgent, TrendSynthesisAgent, AlertPrioritizationAgent
from config import Config
import time

logger = logging.getLogger(__name__)

class AIProcessingPipeline:
    """Pipeline for processing content with AI agents"""
    
    def __init__(self):
        self.content_quality_agent = ContentQualityAgent()
        self.summary_agent = SummaryAgent()
        self.trend_synthesis_agent = TrendSynthesisAgent()
        self.alert_prioritization_agent = AlertPrioritizationAgent()
        
        self.batch_size = Config.MAX_ARTICLES_PER_BATCH
        self.processing_delay = 1  # seconds between requests to avoid rate limits
    
    def process_unprocessed_articles(self):
        """Process articles that haven't been analyzed by AI yet"""
        unprocessed = Article.query.filter_by(ai_processed=False).limit(self.batch_size).all()
        
        if not unprocessed:
            logger.info("No unprocessed articles found")
            return 0
        
        logger.info(f"Processing {len(unprocessed)} articles with AI agents")
        processed_count = 0
        
        for article in unprocessed:
            try:
                self.process_article(article)
                processed_count += 1
                
                # Add delay to respect rate limits
                time.sleep(self.processing_delay)
                
            except Exception as e:
                logger.error(f"Failed to process article {article.id}: {str(e)}")
                # Mark as processed with error
                article.ai_processed = True
                article.ai_processing_errors = str(e)
                article.ai_processing_date = datetime.utcnow()
                db.session.commit()
        
        logger.info(f"Completed AI processing for {processed_count} articles")
        return processed_count
    
    def process_article(self, article):
        """Process a single article with AI agents"""
        article_data = {
            'title': article.title,
            'content': article.content,
            'author': article.author,
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'category': article.category
        }
        
        try:
            # Content Quality Analysis
            quality_result = self.content_quality_agent.process(article_data)
            if quality_result:
                article.quality_score = quality_result.get('quality_score')
            
            # Summarization
            summary_result = self.summary_agent.process(article_data)
            if summary_result:
                article.ai_summary = summary_result.get('summary')
            
            # Mark as processed
            article.ai_processed = True
            article.ai_processing_date = datetime.utcnow()
            article.ai_processing_errors = None
            
            db.session.commit()
            
            logger.debug(f"Successfully processed article {article.id}")
            
        except Exception as e:
            logger.error(f"Error processing article {article.id}: {str(e)}")
            raise
    
    def process_reddit_posts(self):
        """Process unprocessed Reddit posts"""
        unprocessed = RedditPost.query.filter_by(ai_processed=False).limit(self.batch_size).all()
        
        if not unprocessed:
            return 0
        
        logger.info(f"Processing {len(unprocessed)} Reddit posts with AI agents")
        processed_count = 0
        
        for post in unprocessed:
            try:
                post_data = {
                    'title': post.title,
                    'content': post.content or '',
                    'author': post.author,
                    'subreddit': post.subreddit,
                    'score': post.score,
                    'category': post.category
                }
                
                # Content Quality Analysis
                quality_result = self.content_quality_agent.process(post_data)
                if quality_result:
                    post.quality_score = quality_result.get('quality_score')
                
                # Summarization (if content is substantial)
                if post.content and len(post.content) > 100:
                    summary_result = self.summary_agent.process(post_data)
                    if summary_result:
                        post.ai_summary = summary_result.get('summary')
                
                post.ai_processed = True
                post.ai_processing_date = datetime.utcnow()
                processed_count += 1
                
                time.sleep(self.processing_delay)
                
            except Exception as e:
                logger.error(f"Failed to process Reddit post {post.id}: {str(e)}")
                post.ai_processed = True
                post.ai_processing_errors = str(e)
                post.ai_processing_date = datetime.utcnow()
        
        db.session.commit()
        return processed_count
    
    def process_trending_analysis(self):
        """Analyze current trends for insights"""
        # Get recent trends from last 24 hours
        cutoff_date = datetime.utcnow() - timedelta(days=1)
        recent_trends = Trend.query.filter(
            Trend.collected_date >= cutoff_date,
            Trend.ai_processed == False
        ).limit(20).all()
        
        if not recent_trends:
            return 0
        
        # Group trends by category for analysis
        categories = {}
        for trend in recent_trends:
            category = trend.category
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'keyword': trend.keyword,
                'trend_score': trend.trend_score,
                'region': trend.region,
                'category': trend.category
            })
        
        processed_count = 0
        
        for category, trend_list in categories.items():
            try:
                # Analyze trends in this category
                synthesis_result = self.trend_synthesis_agent.process(trend_list)
                
                if synthesis_result and synthesis_result.get('analysis'):
                    # Create or update trend analysis alert
                    alert_title = f"Trend Analysis: {category.title()} Category"
                    alert_message = synthesis_result.get('analysis', '')
                    
                    # Check if similar alert exists recently
                    recent_alert = Alert.query.filter(
                        Alert.title.like(f"%Trend Analysis: {category.title()}%"),
                        Alert.created_at >= datetime.utcnow() - timedelta(hours=6)
                    ).first()
                    
                    if not recent_alert:
                        alert = Alert(
                            title=alert_title,
                            message=alert_message,
                            alert_type='trend_analysis',
                            priority='medium',
                            category=category
                        )
                        db.session.add(alert)
                        processed_count += 1
                
                # Mark trends as processed
                for trend in recent_trends:
                    if trend.category == category:
                        trend.ai_processed = True
                        trend.ai_processing_date = datetime.utcnow()
                        trend.trend_analysis = synthesis_result.get('analysis', '') if synthesis_result else ''
                
            except Exception as e:
                logger.error(f"Failed to process trends for category {category}: {str(e)}")
        
        db.session.commit()
        return processed_count
    
    def process_alert_prioritization(self):
        """Process unread alerts for prioritization"""
        unprocessed_alerts = Alert.query.filter(
            Alert.ai_processed == False,
            Alert.is_read == False
        ).limit(10).all()
        
        if not unprocessed_alerts:
            return 0
        
        processed_count = 0
        
        for alert in unprocessed_alerts:
            try:
                alert_data = {
                    'title': alert.title,
                    'message': alert.message,
                    'alert_type': alert.alert_type,
                    'priority': alert.priority,
                    'category': alert.category,
                    'created_at': alert.created_at
                }
                
                prioritization_result = self.alert_prioritization_agent.process(alert_data)
                
                if prioritization_result:
                    alert.ai_priority_score = prioritization_result.get('priority_score')
                    alert.ai_summary = prioritization_result.get('reasoning', '')
                    
                    # Update priority if AI suggests different level
                    recommended_priority = prioritization_result.get('priority_level')
                    if recommended_priority in ['low', 'medium', 'high', 'critical']:
                        alert.priority = recommended_priority
                
                alert.ai_processed = True
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process alert {alert.id}: {str(e)}")
                alert.ai_processed = True
        
        db.session.commit()
        return processed_count
    
    def run_full_pipeline(self):
        """Run the complete AI processing pipeline"""
        logger.info("Starting full AI processing pipeline")
        start_time = time.time()
        
        results = {
            'articles_processed': self.process_unprocessed_articles(),
            'reddit_posts_processed': self.process_reddit_posts(),
            'trend_analyses_created': self.process_trending_analysis(),
            'alerts_prioritized': self.process_alert_prioritization()
        }
        
        processing_time = time.time() - start_time
        logger.info(f"AI pipeline completed in {processing_time:.2f} seconds")
        logger.info(f"Results: {results}")
        
        return results
    
    def get_processing_stats(self):
        """Get statistics about AI processing"""
        total_articles = Article.query.count()
        processed_articles = Article.query.filter_by(ai_processed=True).count()
        
        total_reddit = RedditPost.query.count()
        processed_reddit = RedditPost.query.filter_by(ai_processed=True).count()
        
        total_trends = Trend.query.count()
        processed_trends = Trend.query.filter_by(ai_processed=True).count()
        
        total_alerts = Alert.query.count()
        processed_alerts = Alert.query.filter_by(ai_processed=True).count()
        
        return {
            'articles': {
                'total': total_articles,
                'processed': processed_articles,
                'pending': total_articles - processed_articles
            },
            'reddit_posts': {
                'total': total_reddit,
                'processed': processed_reddit,
                'pending': total_reddit - processed_reddit
            },
            'trends': {
                'total': total_trends,
                'processed': processed_trends,
                'pending': total_trends - processed_trends
            },
            'alerts': {
                'total': total_alerts,
                'processed': processed_alerts,
                'pending': total_alerts - processed_alerts
            }
        }

# Scheduler job function
def scheduled_ai_processing():
    """Function to be called by the scheduler for AI processing"""
    try:
        pipeline = AIProcessingPipeline()
        results = pipeline.run_full_pipeline()
        logger.info(f"Scheduled AI processing completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Scheduled AI processing failed: {str(e)}")
        return {}