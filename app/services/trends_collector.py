from pytrends.request import TrendReq
import logging
from datetime import datetime, timedelta
import json
import time
import random
from app import db
from app.models import Trend
from config import Config

logger = logging.getLogger(__name__)

class TrendsCollector:
    def __init__(self):
        try:
            # Try with newer pytrends API
            self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        except Exception:
            try:
                # Fallback to basic initialization
                self.pytrends = TrendReq(hl='en-US', tz=360)
            except Exception as e:
                logger.error(f"Failed to initialize Google Trends API: {str(e)}")
                self.pytrends = None
        
        # Keywords to track by category
        self.keyword_configs = {
            'ai': [
                'artificial intelligence',
                'machine learning',
                'deep learning',
                'ChatGPT',
                'OpenAI',
                'Claude AI',
                'neural networks',
                'computer vision',
                'natural language processing',
                'LLM'
            ],
            'science': [
                'scientific research',
                'climate change',
                'quantum computing',
                'space exploration',
                'biotechnology',
                'gene therapy',
                'renewable energy',
                'physics breakthrough',
                'medical research',
                'astronomy'
            ],
            'international': [
                'geopolitics',
                'international relations',
                'trade war',
                'diplomacy',
                'foreign policy',
                'global economics',
                'international conflict',
                'world politics',
                'global security',
                'international trade'
            ]
        }
        
        # Google Trends regions to monitor
        self.regions = ['US', 'GB', 'DE', 'JP', 'CN']
        
    def collect_all_trends(self):
        """Collect trends data for all categories and keywords"""
        if not self.pytrends:
            logger.error("Google Trends API not available")
            return 0
            
        total_new_trends = 0
        
        for category, keywords in self.keyword_configs.items():
            try:
                new_trends = self.collect_category_trends(category, keywords)
                total_new_trends += new_trends
                logger.info(f"Collected {new_trends} trends for {category}")
                
                # Add delay between categories to respect rate limits
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error collecting trends for {category}: {str(e)}")
        
        return total_new_trends
    
    def collect_category_trends(self, category, keywords):
        """Collect trends for a specific category"""
        new_trends_count = 0
        
        # Process keywords in batches of 5 (Google Trends API limit)
        batch_size = 5
        for i in range(0, len(keywords), batch_size):
            batch_keywords = keywords[i:i+batch_size]
            
            try:
                new_trends = self.collect_keyword_batch(category, batch_keywords)
                new_trends_count += new_trends
                
                # Add delay between batches
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error collecting batch {batch_keywords}: {str(e)}")
                continue
        
        return new_trends_count
    
    def collect_keyword_batch(self, category, keywords):
        """Collect trends for a batch of keywords"""
        new_trends_count = 0
        
        for region in self.regions:
            try:
                # Build payload for Google Trends
                self.pytrends.build_payload(
                    keywords, 
                    cat=0, 
                    timeframe='today 3-m',  # Last 3 months
                    geo=region,
                    gprop=''
                )
                
                # Get interest over time
                interest_over_time = self.pytrends.interest_over_time()
                
                if not interest_over_time.empty:
                    # Process each keyword
                    for keyword in keywords:
                        if keyword in interest_over_time.columns:
                            latest_score = interest_over_time[keyword].iloc[-1] if len(interest_over_time) > 0 else 0
                            
                            # Create trend entry
                            trend = self._create_trend_entry(
                                keyword=keyword,
                                category=category,
                                region=region,
                                trend_score=float(latest_score),
                                timeframe='today 3-m'
                            )
                            
                            if trend:
                                db.session.add(trend)
                                new_trends_count += 1
                
                # Get related topics if available
                try:
                    related_topics = self.pytrends.related_topics()
                    if related_topics:
                        # Store related topics for analysis
                        for keyword in keywords:
                            if keyword in related_topics and related_topics[keyword]['top'] is not None:
                                related_data = related_topics[keyword]['top'].head(5)
                                if not related_data.empty:
                                    self._update_trend_with_related_topics(keyword, category, region, related_data)
                except Exception as e:
                    logger.debug(f"Could not get related topics: {str(e)}")
                
                # Delay between regions
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"Error collecting trends for region {region}: {str(e)}")
                continue
        
        db.session.commit()
        return new_trends_count
    
    def _create_trend_entry(self, keyword, category, region, trend_score, timeframe):
        """Create a new Trend database entry"""
        try:
            # Check if similar trend exists recently (within last hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            existing_trend = Trend.query.filter(
                Trend.keyword == keyword,
                Trend.region == region,
                Trend.category == category,
                Trend.collected_date >= recent_cutoff
            ).first()
            
            if existing_trend:
                # Update existing trend score
                existing_trend.trend_score = trend_score
                existing_trend.collected_date = datetime.utcnow()
                return None  # Don't count as new
            
            # Create new trend entry
            trend = Trend(
                keyword=keyword,
                search_volume=None,  # Google Trends doesn't provide absolute volume
                trend_score=trend_score,
                region=region,
                timeframe=timeframe,
                category=category,
                collected_date=datetime.utcnow()
            )
            
            return trend
            
        except Exception as e:
            logger.error(f"Error creating trend entry: {str(e)}")
            return None
    
    def _update_trend_with_related_topics(self, keyword, category, region, related_data):
        """Update trend with related topics information"""
        try:
            # Find the most recent trend for this keyword
            trend = Trend.query.filter(
                Trend.keyword == keyword,
                Trend.region == region,
                Trend.category == category
            ).order_by(Trend.collected_date.desc()).first()
            
            if trend:
                # Convert related topics to JSON
                related_topics = []
                for _, row in related_data.iterrows():
                    related_topics.append({
                        'topic': row.get('topic_title', ''),
                        'value': row.get('value', 0)
                    })
                
                trend.related_topics = json.dumps(related_topics)
                
        except Exception as e:
            logger.error(f"Error updating related topics: {str(e)}")
    
    def get_trending_keywords(self, category=None, region='US', limit=10):
        """Get currently trending keywords"""
        query = Trend.query.filter(
            Trend.region == region,
            Trend.collected_date >= datetime.utcnow() - timedelta(days=1)
        )
        
        if category:
            query = query.filter(Trend.category == category)
        
        trends = query.order_by(Trend.trend_score.desc()).limit(limit).all()
        return trends
    
    def get_trend_analysis(self, keyword, days=30):
        """Get trend analysis for a specific keyword over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        trends = Trend.query.filter(
            Trend.keyword == keyword,
            Trend.collected_date >= cutoff_date
        ).order_by(Trend.collected_date.asc()).all()
        
        if not trends:
            return None
        
        # Calculate trend direction
        if len(trends) >= 2:
            recent_avg = sum(t.trend_score for t in trends[-3:]) / min(3, len(trends))
            older_avg = sum(t.trend_score for t in trends[:3]) / min(3, len(trends))
            trend_direction = 'rising' if recent_avg > older_avg else 'falling'
        else:
            trend_direction = 'stable'
        
        return {
            'keyword': keyword,
            'data_points': len(trends),
            'latest_score': trends[-1].trend_score,
            'peak_score': max(t.trend_score for t in trends),
            'trend_direction': trend_direction,
            'time_span': f"{days} days"
        }

# Scheduler job function
def scheduled_trends_collection():
    """Function to be called by the scheduler"""
    try:
        collector = TrendsCollector()
        new_trends = collector.collect_all_trends()
        logger.info(f"Scheduled trends collection completed: {new_trends} new trend entries")
        return new_trends
    except Exception as e:
        logger.error(f"Scheduled trends collection failed: {str(e)}")
        return 0