import pytest
import tempfile
import os
from app import create_app, db
from app.models import Source, Article, RedditPost, Trend


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'ENABLE_AI_AGENTS': False,  # Disable AI agents for testing
        'RSS_COLLECTION_INTERVAL': 1,  # Short intervals for testing
        'REDDIT_COLLECTION_INTERVAL': 1,
        'TRENDS_COLLECTION_INTERVAL': 1,
        'LOG_TO_FILE': False  # Don't create log files during testing
    }
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_source():
    """Create a sample RSS source"""
    source = Source(
        name='Test Feed',
        url='https://example.com/feed.xml',
        source_type='rss',
        category='test',
        is_active=True
    )
    db.session.add(source)
    db.session.commit()
    return source


@pytest.fixture
def sample_article(sample_source):
    """Create a sample article"""
    article = Article(
        title='Test Article',
        url='https://example.com/article',
        content='This is a test article content.',
        author='Test Author',
        category='test',
        source_id=sample_source.id,
        sentiment_score=0.5,
        view_count=0
    )
    db.session.add(article)
    db.session.commit()
    return article


@pytest.fixture
def sample_reddit_post():
    """Create a sample Reddit post"""
    post = RedditPost(
        title='Test Reddit Post',
        url='https://reddit.com/r/test/post',
        content='This is a test Reddit post.',
        author='test_user',
        subreddit='test',
        score=100,
        num_comments=10,
        reddit_id='test123'
    )
    db.session.add(post)
    db.session.commit()
    return post


@pytest.fixture
def sample_trend():
    """Create a sample trend"""
    trend = Trend(
        keyword='test keyword',
        region='US',
        category='technology',
        trend_score=75.5,
        search_volume=1000
    )
    db.session.add(trend)
    db.session.commit()
    return trend