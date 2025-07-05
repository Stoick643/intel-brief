import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'source_type'):
            log_entry['source_type'] = record.source_type
        if hasattr(record, 'articles_processed'):
            log_entry['articles_processed'] = record.articles_processed
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        if hasattr(record, 'ai_agent_type'):
            log_entry['ai_agent_type'] = record.ai_agent_type
        if hasattr(record, 'cost_estimate'):
            log_entry['cost_estimate'] = record.cost_estimate
        
        return json.dumps(log_entry)


def setup_logging(app):
    """Set up comprehensive logging for the application"""
    
    # Get configuration
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    log_to_file = app.config.get('LOG_TO_FILE', True)
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Console handler with colored output for development
    console_handler = logging.StreamHandler(sys.stdout)
    if app.config.get('FLASK_ENV') == 'development':
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        console_handler.setFormatter(logging.Formatter(console_format))
    else:
        # Use structured logging in production
        console_handler.setFormatter(StructuredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handlers for production
    if log_to_file:
        # Main application log with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # Error log - separate file for errors only
        error_log_file = str(log_dir / 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
        
        # Data collection log - separate file for collection activities
        collection_log_file = str(log_dir / 'collection.log')
        collection_handler = logging.handlers.RotatingFileHandler(
            collection_log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        collection_handler.addFilter(CollectionLogFilter())
        collection_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(collection_handler)
        
        # AI processing log - separate file for AI activities
        ai_log_file = str(log_dir / 'ai_processing.log')
        ai_handler = logging.handlers.RotatingFileHandler(
            ai_log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        ai_handler.addFilter(AIProcessingLogFilter())
        ai_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(ai_handler)
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    app.logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")


class CollectionLogFilter(logging.Filter):
    """Filter for data collection related logs"""
    
    def filter(self, record):
        return (
            'collector' in record.name.lower() or 
            'collection' in record.getMessage().lower() or
            hasattr(record, 'source_type')
        )


class AIProcessingLogFilter(logging.Filter):
    """Filter for AI processing related logs"""
    
    def filter(self, record):
        return (
            'ai' in record.name.lower() or 
            'agent' in record.name.lower() or
            hasattr(record, 'ai_agent_type')
        )


def get_logger(name):
    """Get a logger with consistent configuration"""
    return logging.getLogger(name)


def log_data_collection(logger, source_type, articles_count, processing_time, success=True):
    """Log data collection activity with structured data"""
    logger.info(
        f"Data collection completed: {source_type}",
        extra={
            'source_type': source_type,
            'articles_processed': articles_count,
            'processing_time': processing_time,
            'success': success
        }
    )


def log_ai_processing(logger, agent_type, articles_count, processing_time, cost_estimate, success=True):
    """Log AI processing activity with structured data"""
    logger.info(
        f"AI processing completed: {agent_type}",
        extra={
            'ai_agent_type': agent_type,
            'articles_processed': articles_count,
            'processing_time': processing_time,
            'cost_estimate': cost_estimate,
            'success': success
        }
    )


def log_request(logger, request, response_status, processing_time):
    """Log HTTP request with structured data"""
    logger.info(
        f"{request.method} {request.path} - {response_status}",
        extra={
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'response_status': response_status,
            'processing_time': processing_time
        }
    )