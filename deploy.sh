#!/bin/bash

# Intelligence Briefing System - Production Deployment Script
# Usage: ./deploy.sh [production|staging|development]

set -e  # Exit on any error

ENVIRONMENT=${1:-production}
APP_NAME="intel-brief"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Starting deployment for environment: $ENVIRONMENT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log_warning "Please edit .env file with your configuration before running again."
            exit 1
        else
            log_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Create necessary directories
create_directories() {
    log_step "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p ssl
    mkdir -p $BACKUP_DIR
    
    log_info "Directories created ✓"
}

# Generate SSL certificates for development/staging
generate_ssl_certs() {
    if [ "$ENVIRONMENT" != "production" ]; then
        log_step "Generating self-signed SSL certificates for $ENVIRONMENT..."
        
        if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
            openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
            log_info "SSL certificates generated ✓"
        else
            log_info "SSL certificates already exist ✓"
        fi
    else
        log_warning "Production deployment detected. Please ensure you have valid SSL certificates in ssl/ directory."
    fi
}

# Database backup
backup_database() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_step "Creating database backup..."
        
        # Check if database container is running
        if docker-compose ps db | grep -q "Up"; then
            docker-compose exec -T db pg_dump -U intel_brief intel_brief_db > $BACKUP_DIR/db_backup_$TIMESTAMP.sql
            log_info "Database backup created: $BACKUP_DIR/db_backup_$TIMESTAMP.sql ✓"
        else
            log_warning "Database container not running. Skipping backup."
        fi
    fi
}

# Build and deploy
build_and_deploy() {
    log_step "Building and deploying application..."
    
    # Pull latest images
    docker-compose pull
    
    # Build application image
    docker-compose build app
    
    # Stop existing containers
    log_step "Stopping existing containers..."
    docker-compose down
    
    # Start new containers
    log_step "Starting new containers..."
    docker-compose up -d
    
    log_info "Application deployed ✓"
}

# Wait for services
wait_for_services() {
    log_step "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for database..."
    for i in {1..30}; do
        if docker-compose exec -T db pg_isready -U intel_brief -d intel_brief_db &> /dev/null; then
            log_info "Database is ready ✓"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Database failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Wait for application
    log_info "Waiting for application..."
    for i in {1..60}; do
        if curl -f http://localhost:5000/health/check &> /dev/null; then
            log_info "Application is ready ✓"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Application failed to start within 60 seconds"
            exit 1
        fi
        sleep 1
    done
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    
    docker-compose exec app flask db upgrade
    
    log_info "Database migrations completed ✓"
}

# Initialize application data
initialize_data() {
    log_step "Initializing application data..."
    
    # Seed the database with initial sources
    docker-compose exec app python app.py seed-db
    
    log_info "Application data initialized ✓"
}

# Health check
health_check() {
    log_step "Performing health check..."
    
    # Check application health
    HEALTH_RESPONSE=$(curl -s http://localhost:5000/health/detailed)
    if echo "$HEALTH_RESPONSE" | grep -q '"status": "healthy"'; then
        log_info "Application health check passed ✓"
    else
        log_error "Application health check failed"
        echo "$HEALTH_RESPONSE"
        exit 1
    fi
    
    # Check if data collection is working
    log_step "Testing data collection..."
    docker-compose exec app python -c "
from app.services.rss_collector import RSSCollector
collector = RSSCollector()
articles = collector.collect_feeds()
print(f'Collected {articles} articles')
"
    
    log_info "Data collection test completed ✓"
}

# Show deployment summary
show_summary() {
    log_step "Deployment Summary"
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "Application URLs:"
    echo "  - Main application: http://localhost:5000"
    echo "  - Health check: http://localhost:5000/health/check"
    echo "  - Detailed health: http://localhost:5000/health/detailed"
    echo "  - Metrics: http://localhost:5000/health/metrics"
    echo ""
    echo "Database:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Database: intel_brief_db"
    echo "  - User: intel_brief"
    echo ""
    echo "Redis:"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "Logs:"
    echo "  - Application logs: ./logs/"
    echo "  - Docker logs: docker-compose logs -f"
    echo ""
    echo "Management commands:"
    echo "  - View logs: docker-compose logs -f app"
    echo "  - Shell access: docker-compose exec app bash"
    echo "  - Database shell: docker-compose exec db psql -U intel_brief intel_brief_db"
    echo "  - Stop services: docker-compose down"
    echo "  - Restart services: docker-compose restart"
    echo ""
    
    if [ "$ENVIRONMENT" != "production" ]; then
        echo "⚠️  This is a $ENVIRONMENT deployment with self-signed SSL certificates."
        echo "   Your browser will show security warnings - this is expected."
    fi
}

# Cleanup on failure
cleanup_on_failure() {
    log_error "Deployment failed. Cleaning up..."
    docker-compose down
    exit 1
}

# Set trap for cleanup
trap cleanup_on_failure ERR

# Main deployment flow
main() {
    echo "Intelligence Briefing System - Deployment Script"
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    
    check_prerequisites
    create_directories
    generate_ssl_certs
    backup_database
    build_and_deploy
    wait_for_services
    run_migrations
    initialize_data
    health_check
    show_summary
}

# Run main function
main