import pytest
from datetime import datetime
from app.models import Source, Article, RedditPost, Trend, Alert, UserFeedback, AgentAnalysis


def test_source_model(app):
    """Test Source model"""
    with app.app_context():
        source = Source(
            name='Test Source',
            url='https://example.com/feed.xml',
            source_type='rss',
            category='test',
            is_active=True
        )
        
        assert source.name == 'Test Source'
        assert source.url == 'https://example.com/feed.xml'
        assert source.source_type == 'rss'
        assert source.is_active is True


def test_article_model(app, sample_source):
    """Test Article model"""
    with app.app_context():
        article = Article(
            title='Test Article',
            url='https://example.com/article',
            content='Test content',
            author='Test Author',
            category='test',
            source_id=sample_source.id,
            sentiment_score=0.5
        )
        
        assert article.title == 'Test Article'
        assert article.sentiment_score == 0.5
        assert article.source_id == sample_source.id


def test_reddit_post_model(app):
    """Test RedditPost model"""
    with app.app_context():
        post = RedditPost(
            title='Test Post',
            url='https://reddit.com/post',
            content='Test content',
            author='test_user',
            subreddit='test',
            score=100,
            num_comments=10,
            reddit_id='test123'
        )
        
        assert post.title == 'Test Post'
        assert post.subreddit == 'test'
        assert post.score == 100
        assert post.reddit_id == 'test123'


def test_trend_model(app):
    """Test Trend model"""
    with app.app_context():
        trend = Trend(
            keyword='test keyword',
            region='US',
            category='technology',
            trend_score=75.5,
            search_volume=1000
        )
        
        assert trend.keyword == 'test keyword'
        assert trend.region == 'US'
        assert trend.trend_score == 75.5


def test_alert_model(app, sample_article):
    """Test Alert model"""
    with app.app_context():
        alert = Alert(
            title='Test Alert',
            message='Test alert message',
            alert_type='info',
            priority='medium',
            article_id=sample_article.id,
            is_read=False
        )
        
        assert alert.title == 'Test Alert'
        assert alert.alert_type == 'info'
        assert alert.priority == 'medium'
        assert alert.is_read is False


def test_user_feedback_model(app, sample_article):
    """Test UserFeedback model"""
    with app.app_context():
        feedback = UserFeedback(
            feedback_type='rating',
            rating=5,
            comment='Great article!',
            article_id=sample_article.id,
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        assert feedback.feedback_type == 'rating'
        assert feedback.rating == 5
        assert feedback.comment == 'Great article!'


def test_agent_analysis_model(app, sample_article):
    """Test AgentAnalysis model"""
    with app.app_context():
        analysis = AgentAnalysis(
            agent_type='content_quality',
            article_id=sample_article.id,
            input_data={'title': 'Test'},
            output_data={'score': 0.8},
            processing_time=1.5,
            success=True,
            cost_estimate=0.001
        )
        
        assert analysis.agent_type == 'content_quality'
        assert analysis.success is True
        assert analysis.processing_time == 1.5
        assert analysis.cost_estimate == 0.001


def test_model_relationships(app, sample_source, sample_article):
    """Test model relationships"""
    with app.app_context():
        # Test source-article relationship
        assert sample_article.source == sample_source
        assert sample_article in sample_source.articles


def test_model_timestamps(app, sample_article):
    """Test automatic timestamp creation"""
    with app.app_context():
        assert sample_article.collected_date is not None
        assert isinstance(sample_article.collected_date, datetime)


def test_model_string_representations(app, sample_source, sample_article):
    """Test string representations of models"""
    with app.app_context():
        assert 'Test Feed' in str(sample_source)
        assert 'Test Article' in str(sample_article)