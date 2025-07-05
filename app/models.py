from datetime import datetime
from app import db

class Source(db.Model):
    __tablename__ = 'sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # 'rss', 'reddit', 'trends'
    category = db.Column(db.String(50), nullable=False)  # 'ai', 'science', 'international'
    is_active = db.Column(db.Boolean, default=True)
    last_collected = db.Column(db.DateTime)
    collection_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    articles = db.relationship('Article', backref='source', lazy=True)
    reddit_posts = db.relationship('RedditPost', backref='source', lazy=True)

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(1000), nullable=False, unique=True)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    author = db.Column(db.String(200))
    published_date = db.Column(db.DateTime)
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    
    # AI Analysis Fields
    quality_score = db.Column(db.Float)  # 0-1 score from ContentQualityAgent
    ai_summary = db.Column(db.Text)  # AI-generated summary
    sentiment_score = db.Column(db.Float)  # -1 to 1 sentiment
    key_topics = db.Column(db.Text)  # JSON string of extracted topics
    ai_processed = db.Column(db.Boolean, default=False)
    ai_processing_date = db.Column(db.DateTime)
    ai_processing_errors = db.Column(db.Text)
    
    # User interaction
    user_rating = db.Column(db.Integer)  # 1-5 rating
    user_feedback = db.Column(db.Text)
    view_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    
    # Relationships
    agent_analyses = db.relationship('AgentAnalysis', backref='article', lazy=True)
    user_feedbacks = db.relationship('UserFeedback', backref='article', lazy=True)

class RedditPost(db.Model):
    __tablename__ = 'reddit_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    reddit_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(1000))
    content = db.Column(db.Text)
    author = db.Column(db.String(100))
    subreddit = db.Column(db.String(100))
    score = db.Column(db.Integer)
    num_comments = db.Column(db.Integer)
    created_utc = db.Column(db.DateTime)
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    
    # AI Analysis Fields
    quality_score = db.Column(db.Float)
    ai_summary = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    key_topics = db.Column(db.Text)
    ai_processed = db.Column(db.Boolean, default=False)
    ai_processing_date = db.Column(db.DateTime)
    ai_processing_errors = db.Column(db.Text)
    
    # User interaction
    user_rating = db.Column(db.Integer)
    user_feedback = db.Column(db.Text)
    view_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    
    # Relationships
    agent_analyses = db.relationship('AgentAnalysis', backref='reddit_post', lazy=True)
    user_feedbacks = db.relationship('UserFeedback', backref='reddit_post', lazy=True)

class Trend(db.Model):
    __tablename__ = 'trends'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200), nullable=False)
    search_volume = db.Column(db.Integer)
    trend_score = db.Column(db.Float)
    region = db.Column(db.String(10), default='US')
    timeframe = db.Column(db.String(50), default='today 5-y')
    collected_date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    
    # AI Analysis Fields
    trend_analysis = db.Column(db.Text)  # AI analysis of trend significance
    related_topics = db.Column(db.Text)  # JSON string
    ai_processed = db.Column(db.Boolean, default=False)
    ai_processing_date = db.Column(db.DateTime)
    
    # Relationships
    agent_analyses = db.relationship('AgentAnalysis', backref='trend', lazy=True)

class AgentAnalysis(db.Model):
    __tablename__ = 'agent_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)  # 'content_quality', 'trend_synthesis', 'summary', 'alert_prioritization'
    input_data = db.Column(db.Text)  # JSON string of input data
    output_data = db.Column(db.Text)  # JSON string of analysis results
    processing_time = db.Column(db.Float)  # seconds
    token_usage = db.Column(db.Integer)  # API tokens used
    cost_estimate = db.Column(db.Float)  # estimated cost in USD
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys (one of these will be populated)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    reddit_post_id = db.Column(db.Integer, db.ForeignKey('reddit_posts.id'))
    trend_id = db.Column(db.Integer, db.ForeignKey('trends.id'))
    
    # Relationships
    performance_metrics = db.relationship('AgentPerformance', backref='analysis', lazy=True)

class AgentPerformance(db.Model):
    __tablename__ = 'agent_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    avg_processing_time = db.Column(db.Float, default=0.0)
    user_satisfaction_score = db.Column(db.Float)  # Based on feedback
    
    # Foreign keys
    analysis_id = db.Column(db.Integer, db.ForeignKey('agent_analyses.id'))

class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    feedback_type = db.Column(db.String(50), nullable=False)  # 'content_rating', 'ai_accuracy', 'feature_request'
    rating = db.Column(db.Integer)  # 1-5 scale
    comment = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys (one of these will be populated)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    reddit_post_id = db.Column(db.Integer, db.ForeignKey('reddit_posts.id'))
    
    # AI-specific feedback
    ai_agent_type = db.Column(db.String(50))  # Which AI agent this feedback is about
    ai_accuracy_rating = db.Column(db.Integer)  # 1-5 scale for AI accuracy

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'breaking_news', 'trend_spike', 'system_error'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    category = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI Analysis Fields
    ai_priority_score = db.Column(db.Float)  # AI-determined priority score
    ai_summary = db.Column(db.Text)  # AI-generated alert summary
    ai_processed = db.Column(db.Boolean, default=False)
    
    # Related content
    related_articles = db.Column(db.Text)  # JSON string of related article IDs
    related_trends = db.Column(db.Text)  # JSON string of related trend IDs