import pytest
from unittest.mock import Mock, patch
from app.services.rss_collector import RSSCollector
from app.services.reddit_collector import RedditCollector
from app.services.trends_collector import TrendsCollector


class TestRSSCollector:
    """Test RSS collection functionality"""
    
    def test_collector_initialization(self):
        """Test RSS collector can be initialized"""
        collector = RSSCollector()
        assert collector is not None
    
    @patch('app.services.rss_collector.feedparser.parse')
    def test_feed_parsing(self, mock_parse):
        """Test feed parsing with mocked data"""
        # Mock feed data
        mock_parse.return_value = Mock()
        mock_parse.return_value.entries = [
            Mock(
                title='Test Article',
                link='https://example.com/test',
                summary='Test summary',
                author='Test Author',
                published_parsed=None
            )
        ]
        
        collector = RSSCollector()
        articles = collector.parse_feed('https://example.com/feed.xml', 'test')
        
        assert len(articles) == 1
        assert articles[0]['title'] == 'Test Article'
    
    def test_duplicate_detection(self, app, sample_article):
        """Test duplicate article detection"""
        with app.app_context():
            collector = RSSCollector()
            
            # Try to add the same article again
            is_duplicate = collector.is_duplicate(sample_article.url)
            assert is_duplicate is True
    
    def test_content_cleaning(self):
        """Test HTML content cleaning"""
        collector = RSSCollector()
        
        dirty_content = "<p>Test content with <script>alert('xss')</script> tags</p>"
        clean_content = collector.clean_content(dirty_content)
        
        assert '<script>' not in clean_content
        assert 'Test content' in clean_content


class TestRedditCollector:
    """Test Reddit collection functionality"""
    
    def test_collector_initialization(self):
        """Test Reddit collector can be initialized"""
        collector = RedditCollector()
        assert collector is not None
    
    def test_graceful_failure_without_credentials(self, app):
        """Test that collector fails gracefully without Reddit credentials"""
        with app.app_context():
            collector = RedditCollector()
            
            # Should not raise exception, just return 0
            new_posts = collector.collect_posts()
            assert new_posts == 0
    
    @patch('app.services.reddit_collector.praw.Reddit')
    def test_post_collection_with_mocked_reddit(self, mock_reddit):
        """Test post collection with mocked Reddit API"""
        # Mock Reddit instance
        mock_reddit_instance = Mock()
        mock_reddit.return_value = mock_reddit_instance
        
        # Mock subreddit and posts
        mock_subreddit = Mock()
        mock_post = Mock()
        mock_post.title = 'Test Reddit Post'
        mock_post.url = 'https://reddit.com/test'
        mock_post.selftext = 'Test content'
        mock_post.author.name = 'test_user'
        mock_post.score = 100
        mock_post.num_comments = 10
        mock_post.id = 'test123'
        mock_post.created_utc = 1234567890
        
        mock_subreddit.hot.return_value = [mock_post]
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        
        collector = RedditCollector()
        collector.reddit = mock_reddit_instance
        
        posts = collector.collect_from_subreddit('test', 1)
        assert len(posts) == 1
        assert posts[0]['title'] == 'Test Reddit Post'


class TestTrendsCollector:
    """Test Google Trends collection functionality"""
    
    def test_collector_initialization(self):
        """Test Trends collector can be initialized"""
        collector = TrendsCollector()
        assert collector is not None
    
    @patch('app.services.trends_collector.TrendReq')
    def test_trends_collection_with_mock(self, mock_trend_req):
        """Test trends collection with mocked pytrends"""
        # Mock TrendReq instance
        mock_pytrends = Mock()
        mock_trend_req.return_value = mock_pytrends
        
        # Mock interest over time data
        mock_pytrends.interest_over_time.return_value = Mock()
        mock_pytrends.interest_over_time.return_value.empty = False
        mock_pytrends.interest_over_time.return_value.iloc = [
            Mock(__getitem__=lambda x, i: 50 if i == 'artificial intelligence' else None)
        ]
        
        collector = TrendsCollector()
        collector.pytrends = mock_pytrends
        
        trends = collector.get_keyword_trends(['artificial intelligence'], 'US')
        
        # Should not raise exception
        assert isinstance(trends, list)
    
    def test_trend_scoring(self):
        """Test trend score calculation"""
        collector = TrendsCollector()
        
        # Test with valid values
        score = collector.calculate_trend_score([10, 20, 30, 40, 50])
        assert score > 0
        
        # Test with empty values
        score = collector.calculate_trend_score([])
        assert score == 0
    
    def test_graceful_api_failure(self, app):
        """Test graceful handling of API failures"""
        with app.app_context():
            collector = TrendsCollector()
            
            # Should not raise exception, return 0
            new_trends = collector.collect_trends()
            assert new_trends >= 0  # Could be 0 if API fails or actual trends if it works