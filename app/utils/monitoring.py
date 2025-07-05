from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, desc, text
from app import db
from app.models import Article, Source, RedditPost, Trend, AgentAnalysis, AgentPerformance
from app.utils.logging_config import get_logger
import psutil
import os
import time


monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/health')
logger = get_logger(__name__)


@monitoring_bp.route('/check')
def health_check():
    """Basic health check endpoint"""
    try:
        # Database connectivity check
        db.session.execute(text('SELECT 1'))
        
        # Get basic system info
        system_info = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0',
            'environment': current_app.config.get('FLASK_ENV', 'production')
        }
        
        return jsonify(system_info), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 503


@monitoring_bp.route('/detailed')
def detailed_health():
    """Detailed health check with system metrics"""
    try:
        start_time = time.time()
        
        # Database health
        db_health = check_database_health()
        
        # System metrics
        system_metrics = get_system_metrics()
        
        # Application metrics
        app_metrics = get_application_metrics()
        
        # Data collection health
        collection_health = check_collection_health()
        
        # AI processing health
        ai_health = check_ai_health()
        
        processing_time = time.time() - start_time
        
        health_data = {
            'status': 'healthy' if all([
                db_health['healthy'],
                system_metrics['healthy'],
                collection_health['healthy']
            ]) else 'degraded',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'processing_time': round(processing_time, 3),
            'database': db_health,
            'system': system_metrics,
            'application': app_metrics,
            'data_collection': collection_health,
            'ai_processing': ai_health
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 500


def check_database_health():
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        
        # Test basic connectivity
        db.session.execute(text('SELECT 1'))
        
        # Test table access
        article_count = Article.query.count()
        source_count = Source.query.count()
        
        query_time = time.time() - start_time
        
        return {
            'healthy': True,
            'query_time': round(query_time, 3),
            'tables_accessible': True,
            'article_count': article_count,
            'source_count': source_count
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'healthy': False,
            'error': str(e)
        }


def get_system_metrics():
    """Get system resource metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process info
        process = psutil.Process()
        
        return {
            'healthy': cpu_percent < 90 and memory.percent < 90,
            'cpu_percent': cpu_percent,
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'percent': round((disk.used / disk.total) * 100, 2)
            },
            'process': {
                'pid': process.pid,
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time()
            }
        }
        
    except Exception as e:
        logger.error(f"System metrics collection failed: {str(e)}")
        return {
            'healthy': False,
            'error': str(e)
        }


def get_application_metrics():
    """Get application-specific metrics"""
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        
        metrics = {
            # Data collection metrics
            'articles': {
                'total': Article.query.count(),
                'today': Article.query.filter(Article.collected_date >= today).count(),
                'this_week': Article.query.filter(Article.collected_date >= week_ago).count(),
                'ai_processed': Article.query.filter_by(ai_processed=True).count()
            },
            'reddit_posts': {
                'total': RedditPost.query.count(),
                'today': RedditPost.query.filter(RedditPost.collected_date >= today).count(),
                'this_week': RedditPost.query.filter(RedditPost.collected_date >= week_ago).count()
            },
            'trends': {
                'total': Trend.query.count(),
                'today': Trend.query.filter(Trend.collected_date >= today).count(),
                'this_week': Trend.query.filter(Trend.collected_date >= week_ago).count()
            },
            
            # AI processing metrics
            'ai_analyses': {
                'total': AgentAnalysis.query.count(),
                'successful': AgentAnalysis.query.filter_by(success=True).count(),
                'today': AgentAnalysis.query.filter(AgentAnalysis.created_at >= today).count(),
                'average_cost': db.session.query(func.avg(AgentAnalysis.cost_estimate)).scalar() or 0
            },
            
            # Source health
            'sources': {
                'total': Source.query.count(),
                'active': Source.query.filter_by(is_active=True).count(),
                'rss_feeds': Source.query.filter_by(source_type='rss', is_active=True).count()
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Application metrics collection failed: {str(e)}")
        return {'error': str(e)}


def check_collection_health():
    """Check data collection health and recent activity"""
    try:
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        # Check recent RSS collection
        recent_articles = Article.query.filter(Article.collected_date >= last_hour).count()
        
        # Check recent Reddit collection
        recent_reddit = RedditPost.query.filter(RedditPost.collected_date >= last_hour).count()
        
        # Check recent Trends collection
        recent_trends = Trend.query.filter(Trend.collected_date >= last_hour).count()
        
        # Check for stale data (no collection in last 2 hours)
        last_article = Article.query.order_by(desc(Article.collected_date)).first()
        hours_since_last_collection = 0
        if last_article:
            hours_since_last_collection = (now - last_article.collected_date).total_seconds() / 3600
        
        collection_healthy = hours_since_last_collection < 2  # Less than 2 hours since last collection
        
        return {
            'healthy': collection_healthy,
            'recent_activity': {
                'articles_last_hour': recent_articles,
                'reddit_posts_last_hour': recent_reddit,
                'trends_last_hour': recent_trends,
                'hours_since_last_collection': round(hours_since_last_collection, 2)
            },
            'last_collection_time': last_article.collected_date.isoformat() + 'Z' if last_article else None
        }
        
    except Exception as e:
        logger.error(f"Collection health check failed: {str(e)}")
        return {
            'healthy': False,
            'error': str(e)
        }


def check_ai_health():
    """Check AI processing health and performance"""
    try:
        now = datetime.utcnow()
        last_day = now - timedelta(days=1)
        
        # Recent AI analyses
        recent_analyses = AgentAnalysis.query.filter(AgentAnalysis.created_at >= last_day).count()
        successful_analyses = AgentAnalysis.query.filter(
            AgentAnalysis.created_at >= last_day,
            AgentAnalysis.success == True
        ).count()
        
        success_rate = (successful_analyses / recent_analyses * 100) if recent_analyses > 0 else 0
        
        # Average processing time
        avg_processing_time = db.session.query(func.avg(AgentAnalysis.processing_time)).filter(
            AgentAnalysis.created_at >= last_day
        ).scalar() or 0
        
        # Cost tracking
        total_cost_today = db.session.query(func.sum(AgentAnalysis.cost_estimate)).filter(
            AgentAnalysis.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
        ).scalar() or 0
        
        ai_healthy = success_rate >= 80  # At least 80% success rate
        
        return {
            'healthy': ai_healthy,
            'recent_analyses': recent_analyses,
            'success_rate': round(success_rate, 2),
            'average_processing_time': round(avg_processing_time, 2),
            'cost_today': round(total_cost_today, 4),
            'agents_available': {
                'deepseek': current_app.config.get('DEEPSEEK_API_KEY') is not None,
                'claude': current_app.config.get('CLAUDE_API_KEY') is not None
            }
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return {
            'healthy': False,
            'error': str(e)
        }


@monitoring_bp.route('/metrics')
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    try:
        # Get application metrics
        app_metrics = get_application_metrics()
        system_metrics = get_system_metrics()
        
        metrics = []
        
        # Application metrics
        metrics.append(f"intelligence_brief_articles_total {app_metrics['articles']['total']}")
        metrics.append(f"intelligence_brief_articles_today {app_metrics['articles']['today']}")
        metrics.append(f"intelligence_brief_articles_ai_processed {app_metrics['articles']['ai_processed']}")
        metrics.append(f"intelligence_brief_reddit_posts_total {app_metrics['reddit_posts']['total']}")
        metrics.append(f"intelligence_brief_trends_total {app_metrics['trends']['total']}")
        metrics.append(f"intelligence_brief_ai_analyses_total {app_metrics['ai_analyses']['total']}")
        metrics.append(f"intelligence_brief_ai_analyses_successful {app_metrics['ai_analyses']['successful']}")
        metrics.append(f"intelligence_brief_sources_active {app_metrics['sources']['active']}")
        
        # System metrics
        if 'cpu_percent' in system_metrics:
            metrics.append(f"intelligence_brief_cpu_percent {system_metrics['cpu_percent']}")
            metrics.append(f"intelligence_brief_memory_percent {system_metrics['memory']['percent']}")
            metrics.append(f"intelligence_brief_disk_percent {system_metrics['disk']['percent']}")
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return f"# Error collecting metrics: {str(e)}", 500, {'Content-Type': 'text/plain'}


@monitoring_bp.route('/logs/<log_type>')
def get_recent_logs(log_type):
    """Get recent log entries"""
    try:
        log_dir = current_app.config.get('LOG_FILE', 'logs/app.log')
        log_dir = os.path.dirname(log_dir)
        
        log_files = {
            'app': 'app.log',
            'error': 'error.log',
            'collection': 'collection.log',
            'ai': 'ai_processing.log'
        }
        
        if log_type not in log_files:
            return jsonify({'error': 'Invalid log type'}), 400
        
        log_file_path = os.path.join(log_dir, log_files[log_type])
        
        if not os.path.exists(log_file_path):
            return jsonify({'logs': [], 'message': 'Log file not found'}), 404
        
        # Read last 100 lines
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines
        
        return jsonify({
            'log_type': log_type,
            'lines': len(recent_lines),
            'logs': [line.strip() for line in recent_lines]
        })
        
    except Exception as e:
        logger.error(f"Log retrieval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500