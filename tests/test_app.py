import pytest
from app import create_app, db
from app.models import Article, Source


def test_app_creation():
    """Test that app can be created"""
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is False


def test_database_connection(app):
    """Test database connectivity"""
    with app.app_context():
        # Test basic database operations
        source_count = Source.query.count()
        assert source_count >= 0  # Should not fail


def test_dashboard_route(client):
    """Test dashboard route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Intelligence Briefing' in response.data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health/check')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert 'timestamp' in json_data


def test_detailed_health_check(client):
    """Test detailed health check"""
    response = client.get('/health/detailed')
    assert response.status_code in [200, 503]  # Healthy or degraded
    
    json_data = response.get_json()
    assert 'database' in json_data
    assert 'system' in json_data
    assert 'application' in json_data


def test_ai_section(client):
    """Test AI section route"""
    response = client.get('/ai')
    assert response.status_code == 200


def test_science_section(client):
    """Test science section route"""
    response = client.get('/science')
    assert response.status_code == 200


def test_international_section(client):
    """Test international section route"""
    response = client.get('/international')
    assert response.status_code == 200


def test_article_detail_404(client):
    """Test article detail with non-existent ID"""
    response = client.get('/article/99999')
    assert response.status_code == 404


def test_article_detail_existing(client, sample_article):
    """Test article detail with existing article"""
    response = client.get(f'/article/{sample_article.id}')
    assert response.status_code == 200
    assert sample_article.title.encode() in response.data


def test_api_stats(client):
    """Test API stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert 'total_articles' in json_data
    assert 'total_sources' in json_data


def test_sources_status(client):
    """Test sources status page"""
    response = client.get('/sources')
    assert response.status_code == 200


def test_api_collect_rss(client):
    """Test RSS collection API endpoint"""
    response = client.post('/api/collect-rss')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['success'] is True
    assert 'new_articles' in json_data


def test_security_headers(client):
    """Test that security headers are present"""
    response = client.get('/')
    
    # Check for security headers
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'X-XSS-Protection' in response.headers


def test_prometheus_metrics(client):
    """Test Prometheus metrics endpoint"""
    response = client.get('/health/metrics')
    assert response.status_code == 200
    assert response.content_type == 'text/plain; charset=utf-8'
    
    # Check for expected metrics
    assert b'intelligence_brief_articles_total' in response.data