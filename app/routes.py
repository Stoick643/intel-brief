from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app import db
from app.models import Article, Source, RedditPost, Trend, Alert, UserFeedback, AgentAnalysis, AgentPerformance
from app.services.rss_collector import RSSCollector, scheduled_rss_collection
from app.services.reddit_collector import RedditCollector, scheduled_reddit_collection
from app.services.trends_collector import TrendsCollector, scheduled_trends_collection
from app.services.ai_pipeline import AIProcessingPipeline, scheduled_ai_processing
from app.services.ai_agents import ContentQualityAgent, SummaryAgent, TrendSynthesisAgent, AlertPrioritizationAgent
import json

main = Blueprint('main', __name__)

@main.route('/')
def dashboard():
    """Main dashboard"""
    # Get recent articles
    recent_articles = Article.query.order_by(desc(Article.collected_date)).limit(8).all()
    
    # Get recent Reddit posts
    recent_reddit_posts = RedditPost.query.order_by(desc(RedditPost.collected_date)).limit(5).all()
    
    # Get articles by category
    ai_articles = Article.query.filter_by(category='ai').order_by(desc(Article.collected_date)).limit(5).all()
    science_articles = Article.query.filter_by(category='science').order_by(desc(Article.collected_date)).limit(5).all()
    intl_articles = Article.query.filter_by(category='international').order_by(desc(Article.collected_date)).limit(5).all()
    
    # Get trending keywords
    trending_keywords = Trend.query.filter(
        Trend.collected_date >= datetime.utcnow() - timedelta(days=1)
    ).order_by(desc(Trend.trend_score)).limit(10).all()
    
    # Get alerts
    alerts = Alert.query.filter_by(is_read=False).order_by(desc(Alert.created_at)).limit(5).all()
    
    # Get basic stats
    stats = {
        'total_articles': Article.query.count(),
        'total_reddit_posts': RedditPost.query.count(),
        'total_trends': Trend.query.count(),
        'total_sources': Source.query.filter_by(is_active=True).count(),
        'articles_today': Article.query.filter(
            Article.collected_date >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        'active_alerts': Alert.query.filter_by(is_read=False).count()
    }
    
    return render_template('dashboard.html', 
                         recent_articles=recent_articles,
                         recent_reddit_posts=recent_reddit_posts,
                         trending_keywords=trending_keywords,
                         ai_articles=ai_articles,
                         science_articles=science_articles,
                         intl_articles=intl_articles,
                         alerts=alerts,
                         stats=stats)

@main.route('/ai')
def ai_section():
    """AI news section"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    articles = Article.query.filter_by(category='ai').order_by(desc(Article.collected_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('category.html', 
                         articles=articles, 
                         category='AI & Technology',
                         category_key='ai')

@main.route('/science')
def science_section():
    """Science news section"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    articles = Article.query.filter_by(category='science').order_by(desc(Article.collected_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('category.html', 
                         articles=articles, 
                         category='Science',
                         category_key='science')

@main.route('/international')
def international_section():
    """International relations section"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    articles = Article.query.filter_by(category='international').order_by(desc(Article.collected_date)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('category.html', 
                         articles=articles, 
                         category='International Relations',
                         category_key='international')

@main.route('/article/<int:article_id>')
def article_detail(article_id):
    """Article detail page"""
    article = Article.query.get_or_404(article_id)
    
    # Increment view count
    article.view_count += 1
    db.session.commit()
    
    # Get related articles (same category, recent)
    related_articles = Article.query.filter(
        Article.category == article.category,
        Article.id != article.id
    ).order_by(desc(Article.collected_date)).limit(5).all()
    
    return render_template('article_detail.html', 
                         article=article,
                         related_articles=related_articles)

@main.route('/sources')
def sources_status():
    """Sources status page"""
    collector = RSSCollector()
    health_status = collector.get_feed_health()
    
    # Get source statistics
    sources = Source.query.all()
    source_stats = {}
    for source in sources:
        if source.source_type == 'rss':
            article_count = Article.query.filter_by(source_id=source.id).count()
        else:
            article_count = 0
        
        source_stats[source.id] = {
            'total_articles': article_count,
            'last_week': Article.query.filter(
                Article.source_id == source.id,
                Article.collected_date >= datetime.utcnow() - timedelta(days=7)
            ).count() if source.source_type == 'rss' else 0
        }
    
    return render_template('sources.html', 
                         health_status=health_status,
                         source_stats=source_stats)

@main.route('/ai-agents')
def ai_agents_status():
    """AI agents status and performance"""
    # Get recent agent analyses
    recent_analyses = AgentAnalysis.query.order_by(desc(AgentAnalysis.created_at)).limit(20).all()
    
    # Get agent performance summary
    agent_performance = {}
    for agent_type in ['content_quality', 'summary', 'trend_synthesis', 'alert_prioritization']:
        total_analyses = AgentAnalysis.query.filter_by(agent_type=agent_type).count()
        successful_analyses = AgentAnalysis.query.filter_by(agent_type=agent_type, success=True).count()
        avg_processing_time = db.session.query(func.avg(AgentAnalysis.processing_time)).filter_by(agent_type=agent_type).scalar()
        total_cost = db.session.query(func.sum(AgentAnalysis.cost_estimate)).filter_by(agent_type=agent_type).scalar()
        
        agent_performance[agent_type] = {
            'total_analyses': total_analyses or 0,
            'successful_analyses': successful_analyses or 0,
            'success_rate': (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0,
            'avg_processing_time': round(avg_processing_time or 0, 2),
            'total_cost': round(total_cost or 0, 4)
        }
    
    return render_template('ai_agents.html', 
                         recent_analyses=recent_analyses,
                         agent_performance=agent_performance)

@main.route('/alerts')
def alerts_page():
    """Alerts page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    alerts = Alert.query.order_by(desc(Alert.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('alerts.html', alerts=alerts)

@main.route('/api/collect-rss', methods=['POST'])
def api_collect_rss():
    """API endpoint to manually trigger RSS collection"""
    try:
        new_articles = scheduled_rss_collection()
        return jsonify({
            'success': True,
            'message': f'Collected {new_articles} new articles',
            'new_articles': new_articles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main.route('/api/process-ai/<int:article_id>', methods=['POST'])
def api_process_ai(article_id):
    """API endpoint to process article with AI agents"""
    article = Article.query.get_or_404(article_id)
    
    try:
        # Process with content quality agent
        quality_agent = ContentQualityAgent()
        quality_result = quality_agent.process({
            'title': article.title,
            'content': article.content,
            'author': article.author,
            'published_date': article.published_date.isoformat() if article.published_date else None
        })
        
        # Process with summary agent
        summary_agent = SummaryAgent()
        summary_result = summary_agent.process({
            'title': article.title,
            'content': article.content
        })
        
        # Update article with AI results
        article.quality_score = quality_result.get('quality_score')
        article.ai_summary = summary_result.get('summary')
        article.ai_processed = True
        article.ai_processing_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Article processed successfully',
            'quality_score': article.quality_score,
            'ai_summary': article.ai_summary
        })
        
    except Exception as e:
        article.ai_processing_errors = str(e)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main.route('/api/feedback', methods=['POST'])
def api_submit_feedback():
    """API endpoint to submit user feedback"""
    data = request.get_json()
    
    try:
        feedback = UserFeedback(
            feedback_type=data.get('feedback_type'),
            rating=data.get('rating'),
            comment=data.get('comment'),
            article_id=data.get('article_id'),
            reddit_post_id=data.get('reddit_post_id'),
            ai_agent_type=data.get('ai_agent_type'),
            ai_accuracy_rating=data.get('ai_accuracy_rating'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main.route('/api/mark-alert-read/<int:alert_id>', methods=['POST'])
def api_mark_alert_read(alert_id):
    """API endpoint to mark alert as read"""
    alert = Alert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Alert marked as read'
    })

@main.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        'total_articles': Article.query.count(),
        'total_reddit_posts': RedditPost.query.count(),
        'total_trends': Trend.query.count(),
        'total_sources': Source.query.filter_by(is_active=True).count(),
        'articles_today': Article.query.filter(
            Article.collected_date >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        'active_alerts': Alert.query.filter_by(is_read=False).count(),
        'ai_processed_articles': Article.query.filter_by(ai_processed=True).count(),
        'total_ai_analyses': AgentAnalysis.query.count(),
        'successful_ai_analyses': AgentAnalysis.query.filter_by(success=True).count()
    }
    
    return jsonify(stats)

@main.route('/api/collect-reddit', methods=['POST'])
def api_collect_reddit():
    """API endpoint to manually trigger Reddit collection"""
    try:
        new_posts = scheduled_reddit_collection()
        return jsonify({
            'success': True,
            'message': f'Collected {new_posts} new Reddit posts',
            'new_posts': new_posts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main.route('/api/collect-trends', methods=['POST'])
def api_collect_trends():
    """API endpoint to manually trigger Google Trends collection"""
    try:
        new_trends = scheduled_trends_collection()
        return jsonify({
            'success': True,
            'message': f'Collected {new_trends} new trend entries',
            'new_trends': new_trends
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500