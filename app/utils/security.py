from flask import request, abort, current_app
from functools import wraps
import hashlib
import hmac
import time
from datetime import datetime, timedelta
import logging
import ipaddress
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


def rate_limit_check(limit_per_minute=100):
    """Simple in-memory rate limiting decorator"""
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.config.get('RATE_LIMIT_ENABLED', True):
                return f(*args, **kwargs)
            
            client_ip = get_client_ip()
            current_time = datetime.utcnow()
            
            # Clean old entries (older than 1 minute)
            cutoff_time = current_time - timedelta(minutes=1)
            request_counts[client_ip] = [
                req_time for req_time in request_counts.get(client_ip, [])
                if req_time > cutoff_time
            ]
            
            # Check rate limit
            if len(request_counts.get(client_ip, [])) >= limit_per_minute:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                abort(429)  # Too Many Requests
            
            # Add current request
            request_counts.setdefault(client_ip, []).append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_client_ip():
    """Get the real client IP address"""
    # Check for forwarded headers (when behind proxy/load balancer)
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        # Take the first IP in the chain
        client_ip = forwarded_ips.split(',')[0].strip()
    else:
        client_ip = request.headers.get('X-Real-IP') or request.remote_addr
    
    return client_ip


def validate_allowed_hosts():
    """Validate that the request is coming to an allowed host"""
    allowed_hosts = current_app.config.get('ALLOWED_HOSTS', ['localhost'])
    
    if '*' in allowed_hosts:
        return True
    
    host = request.headers.get('Host', '').split(':')[0]
    
    if host not in allowed_hosts:
        logger.warning(f"Request to unauthorized host: {host}")
        abort(400)
    
    return True


def secure_headers():
    """Add security headers to responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Security headers
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
                # HTTPS enforcement in production
                if current_app.config.get('FORCE_HTTPS', False):
                    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                
                # Content Security Policy
                csp_policy = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' https://cdn.jsdelivr.net;"
                )
                response.headers['Content-Security-Policy'] = csp_policy
            
            return response
        return decorated_function
    return decorator


def validate_api_key(required_key_name=None):
    """Validate API key for protected endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For development, skip API key validation
            if current_app.config.get('FLASK_ENV') == 'development':
                return f(*args, **kwargs)
            
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                logger.warning("API request without key")
                abort(401)
            
            # In a real application, you would validate against a database
            # For now, we'll use a simple configuration-based approach
            valid_keys = current_app.config.get('API_KEYS', [])
            
            if api_key not in valid_keys:
                logger.warning(f"Invalid API key used: {api_key[:8]}...")
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_input(input_string, max_length=1000):
    """Sanitize user input to prevent basic injection attacks"""
    if not input_string:
        return ""
    
    # Truncate to max length
    sanitized = str(input_string)[:max_length]
    
    # Remove potential script tags and SQL injection patterns
    dangerous_patterns = [
        '<script', '</script>', 'javascript:', 'vbscript:',
        'onload=', 'onerror=', 'onclick=', 'onmouseover=',
        'DROP TABLE', 'DELETE FROM', 'INSERT INTO',
        'UPDATE SET', 'UNION SELECT', '--', ';--'
    ]
    
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.lower(), '')
        sanitized = sanitized.replace(pattern.upper(), '')
    
    return sanitized.strip()


def validate_url(url):
    """Validate URL to prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Prevent access to private IP ranges
        if parsed.hostname:
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    logger.warning(f"Attempted access to private IP: {parsed.hostname}")
                    return False
            except ValueError:
                # Not an IP address, allow domain names
                pass
        
        # Block localhost and common private domains
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
        if parsed.hostname in blocked_hosts:
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False


def generate_csrf_token():
    """Generate CSRF token for forms"""
    import secrets
    return secrets.token_urlsafe(32)


def verify_csrf_token(token, session_token):
    """Verify CSRF token"""
    return hmac.compare_digest(token, session_token)


class SecurityMiddleware:
    """Security middleware for Flask application"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Run before each request"""
        # Validate allowed hosts
        validate_allowed_hosts()
        
        # Log suspicious requests
        self.log_suspicious_activity()
    
    def after_request(self, response):
        """Run after each request"""
        # Add security headers
        self.add_security_headers(response)
        return response
    
    def log_suspicious_activity(self):
        """Log potentially suspicious request patterns"""
        suspicious_patterns = [
            'admin', 'wp-admin', '.env', 'config', 'backup',
            'phpinfo', 'shell', 'cmd', 'exec', '../'
        ]
        
        path = request.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path:
                logger.warning(
                    f"Suspicious request pattern detected",
                    extra={
                        'pattern': pattern,
                        'path': request.path,
                        'ip': get_client_ip(),
                        'user_agent': request.headers.get('User-Agent', '')
                    }
                )
                break
    
    def add_security_headers(self, response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        if current_app.config.get('FORCE_HTTPS', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


def init_security(app):
    """Initialize security middleware and settings"""
    # Initialize security middleware
    SecurityMiddleware(app)
    
    # Set secure cookie settings in production
    if app.config.get('FLASK_ENV') == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    logger.info("Security middleware initialized")