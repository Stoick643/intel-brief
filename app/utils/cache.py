from flask import current_app
from functools import wraps
from datetime import datetime, timedelta
import json
import hashlib
import logging


logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache implementation"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key):
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        # Check if expired
        if self._is_expired(key):
            self.delete(key)
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return self.cache[key]
    
    def set(self, key, value, ttl_seconds=300):
        """Set value in cache with TTL"""
        self.cache[key] = value
        self.timestamps[key] = {
            'created': datetime.utcnow(),
            'ttl': ttl_seconds
        }
        logger.debug(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
    
    def delete(self, key):
        """Delete key from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
        logger.debug("Cache cleared")
    
    def _is_expired(self, key):
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        
        timestamp_info = self.timestamps[key]
        expiry_time = timestamp_info['created'] + timedelta(seconds=timestamp_info['ttl'])
        return datetime.utcnow() > expiry_time
    
    def cleanup_expired(self):
        """Clean up expired entries"""
        expired_keys = [key for key in self.cache.keys() if self._is_expired(key)]
        for key in expired_keys:
            self.delete(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self):
        """Get cache statistics"""
        total_keys = len(self.cache)
        expired_keys = len([key for key in self.cache.keys() if self._is_expired(key)])
        
        return {
            'total_keys': total_keys,
            'active_keys': total_keys - expired_keys,
            'expired_keys': expired_keys,
            'memory_usage': sum(len(str(v)) for v in self.cache.values())
        }


# Global cache instance
cache = SimpleCache()


def cached(ttl_seconds=300, key_prefix=''):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(f.__name__, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        return decorated_function
    return decorator


def cache_dashboard_stats(ttl_seconds=60):
    """Cache dashboard statistics with short TTL"""
    return cached(ttl_seconds=ttl_seconds, key_prefix='dashboard_stats')


def cache_article_list(ttl_seconds=300):
    """Cache article lists with medium TTL"""
    return cached(ttl_seconds=ttl_seconds, key_prefix='article_list')


def cache_source_health(ttl_seconds=600):
    """Cache source health checks with longer TTL"""
    return cached(ttl_seconds=ttl_seconds, key_prefix='source_health')


def _generate_cache_key(func_name, args, kwargs, prefix=''):
    """Generate a unique cache key for function call"""
    # Create a string representation of arguments
    key_parts = [prefix, func_name]
    
    # Add args
    for arg in args:
        if hasattr(arg, 'id'):  # Database objects
            key_parts.append(f"obj_{arg.__class__.__name__}_{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):  # Database objects
            key_parts.append(f"{k}_obj_{v.__class__.__name__}_{v.id}")
        else:
            key_parts.append(f"{k}_{v}")
    
    # Create hash of the key to ensure consistent length
    key_string = '_'.join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern"""
    keys_to_delete = [key for key in cache.cache.keys() if pattern in key]
    for key in keys_to_delete:
        cache.delete(key)
    
    logger.debug(f"Invalidated {len(keys_to_delete)} cache keys matching pattern: {pattern}")


def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    try:
        from app.models import Article, Source, RedditPost, Trend
        from sqlalchemy import desc, func
        from app import db
        
        logger.info("Starting cache warming...")
        
        # Warm dashboard stats
        stats = {
            'total_articles': Article.query.count(),
            'total_reddit_posts': RedditPost.query.count(),
            'total_trends': Trend.query.count(),
            'total_sources': Source.query.filter_by(is_active=True).count()
        }
        cache.set('dashboard_stats_warmed', stats, 300)
        
        # Warm recent articles for each category
        categories = ['ai', 'science', 'international']
        for category in categories:
            recent_articles = Article.query.filter_by(category=category)\
                .order_by(desc(Article.collected_date)).limit(10).all()
            cache.set(f'recent_articles_{category}', recent_articles, 300)
        
        # Warm trending keywords
        recent_trends = Trend.query.filter(
            Trend.collected_date >= datetime.utcnow() - timedelta(days=1)
        ).order_by(desc(Trend.trend_score)).limit(10).all()
        cache.set('trending_keywords', recent_trends, 600)
        
        logger.info("Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming failed: {str(e)}")


class CacheConfig:
    """Cache configuration settings"""
    
    # Default TTL values (in seconds)
    DASHBOARD_STATS_TTL = 60        # 1 minute
    ARTICLE_LIST_TTL = 300          # 5 minutes
    SOURCE_HEALTH_TTL = 600         # 10 minutes
    SEARCH_RESULTS_TTL = 1800       # 30 minutes
    USER_PREFERENCES_TTL = 3600     # 1 hour
    STATIC_DATA_TTL = 86400         # 24 hours
    
    # Cache size limits
    MAX_CACHE_KEYS = 1000
    MAX_MEMORY_MB = 100
    
    # Cleanup intervals
    CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


def schedule_cache_cleanup():
    """Schedule periodic cache cleanup"""
    from app import scheduler
    
    def cleanup_job():
        cache.cleanup_expired()
        
        # Enforce cache size limits
        stats = cache.get_stats()
        if stats['total_keys'] > CacheConfig.MAX_CACHE_KEYS:
            # Simple LRU: clear half the cache
            keys_to_remove = list(cache.cache.keys())[:stats['total_keys'] // 2]
            for key in keys_to_remove:
                cache.delete(key)
            logger.info(f"Cache size limit reached, removed {len(keys_to_remove)} keys")
    
    scheduler.add_job(
        func=cleanup_job,
        trigger="interval",
        seconds=CacheConfig.CLEANUP_INTERVAL_SECONDS,
        id='cache_cleanup',
        replace_existing=True
    )
    
    logger.info("Cache cleanup job scheduled")


def get_cache_stats():
    """Get comprehensive cache statistics"""
    stats = cache.get_stats()
    
    # Add configuration info
    stats.update({
        'config': {
            'max_keys': CacheConfig.MAX_CACHE_KEYS,
            'max_memory_mb': CacheConfig.MAX_MEMORY_MB,
            'cleanup_interval': CacheConfig.CLEANUP_INTERVAL_SECONDS
        },
        'hit_rate': 'Not implemented',  # Would need hit/miss counters
        'performance': {
            'memory_usage_mb': stats['memory_usage'] / (1024 * 1024),
            'efficiency': (stats['active_keys'] / stats['total_keys'] * 100) if stats['total_keys'] > 0 else 0
        }
    })
    
    return stats