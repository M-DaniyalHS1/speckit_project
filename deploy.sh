#!/bin/bash
"""
Deployment scripts for the AI-Enhanced Interactive Book Agent Production Environment

This script provides automation for deploying the application to production environments.
It includes functions for building, testing, configuring, and launching the application
with all necessary services and environment-specific configurations.
"""

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration
ENVIRONMENT=${ENVIRONMENT:-production}
PROJECT_NAME="ai-book-agent"
CONTAINER_REGISTRY=${CONTAINER_REGISTRY:-"docker.io/myorg"}
IMAGE_TAG=${IMAGE_TAG:-$(git rev-parse --short HEAD)}
DOMAIN_NAME=${DOMAIN_NAME:-"book-agent.example.com"}
USE_TLS=${USE_TLS:-true}
SSL_CERT_PATH=${SSL_CERT_PATH:-"/etc/ssl/certs/book-agent.crt"}
SSL_KEY_PATH=${SSL_CERT_PATH:-"/etc/ssl/private/book-agent.key"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color


# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}


# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker before proceeding."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose before proceeding."
        exit 1
    fi
    
    if [[ ${EUID} -eq 0 ]]; then
        print_warning "Running as root is not recommended. Consider using a non-root user with docker group membership."
    fi
    
    print_status "Prerequisites check passed"
}


# Build Docker images
build_images() {
    print_status "Building Docker images for ${ENVIRONMENT}..."
    
    docker-compose -f docker-compose.yml build --no-cache
    
    print_status "Docker images built successfully"
}


# Run tests before deployment
run_tests() {
    print_status "Running pre-deployment tests..."
    
    # Run unit tests
    docker-compose -f docker-compose.test.yml run --rm test-runner pytest backend/tests/unit/
    
    # Run integration tests
    docker-compose -f docker-compose.test.yml run --rm test-runner pytest backend/tests/integration/
    
    # Run end-to-end tests if environment is staging
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        docker-compose -f docker-compose.test.yml run --rm test-runner pytest backend/tests/e2e/
    fi
    
    print_status "All tests passed successfully"
}


# Deploy application to production
deploy() {
    print_status "Starting deployment to ${ENVIRONMENT} environment..."
    
    # Pull latest images (in case of rollback)
    print_status "Pulling latest images..."
    docker-compose -f docker-compose.${ENVIRONMENT}.yml pull || true
    
    # Backup current configuration if it exists
    if [ -d "/opt/${PROJECT_NAME}/data" ]; then
        print_status "Creating backup of current deployment..."
        BACKUP_DIR="/opt/${PROJECT_NAME}/backups/backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "${BACKUP_DIR}"
        cp -r /opt/${PROJECT_NAME}/data "${BACKUP_DIR}/"
        print_status "Backup created at ${BACKUP_DIR}"
    fi
    
    # Start the services
    print_status "Deploying services..."
    docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d --force-recreate
    
    # Wait for services to be healthy
    print_status "Waiting for services to become healthy..."
    sleep 10
    
    # Check service health
    check_health
    
    # Run post-deployment health checks
    run_health_checks
    
    print_status "Deployment completed successfully"
}


# Check service health
check_health() {
    print_status "Checking service health..."
    
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        HEALTH_STATUS=$(docker-compose -f docker-compose.${ENVIRONMENT}.yml ps --health 2>/dev/null | grep -c "healthy")
        TOTAL_SERVICES=$(docker-compose -f docker-compose.${ENVIRONMENT}.yml ps 2>/dev/null | grep -c "Up")
        
        if [ $HEALTH_STATUS -eq $TOTAL_SERVICES ]; then
            print_status "All services are healthy"
            return 0
        fi
        
        sleep 10
        ((RETRY_COUNT++))
    done
    
    print_error "Timeout waiting for services to become healthy"
    docker-compose -f docker-compose.${ENVIRONMENT}.yml ps
    exit 1
}


# Run health checks
run_health_checks() {
    print_status "Running post-deployment health checks..."
    
    # Health check endpoint
    HEALTH_CHECK_URL="https://${DOMAIN_NAME}/health"
    RETRY_COUNT=0
    MAX_RETRIES=10
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -k --max-time 10 "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            print_status "Health check passed"
            return 0
        fi
        
        sleep 10
        ((RETRY_COUNT++))
    done
    
    print_error "Health checks failed after ${MAX_RETRIES} attempts"
    exit 1
}


# Create SSL certificates (if needed)
setup_ssl() {
    if [[ "$USE_TLS" == "true" && "$ENVIRONMENT" == "production" ]]; then
        print_status "Setting up SSL certificates..."
        
        if [ ! -f "$SSL_CERT_PATH" ] || [ ! -f "$SSL_KEY_PATH" ]; then
            print_warning "SSL certificates not found. Creating self-signed certificates for testing purposes."
            print_warning "For production, please obtain proper certificates from a Certificate Authority."
            
            mkdir -p "$(dirname "$SSL_CERT_PATH")" "$(dirname "$SSL_KEY_PATH")"
            
            # Generate self-signed certificate (for testing only)
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$SSL_KEY_PATH" \
                -out "$SSL_CERT_PATH" \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN_NAME}"
        fi
    fi
}


# Configure environment
configure_environment() {
    print_status "Configuring environment for ${ENVIRONMENT}..."
    
    # Create necessary directories
    sudo mkdir -p /opt/${PROJECT_NAME}/{data,logs,backups,config}
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/${PROJECT_NAME} << EOF
/opt/${PROJECT_NAME}/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    copytruncate
    notifempty
    create 644 root root
}
EOF
    
    # Verify environment variables
    if [[ -z "${GOOGLE_API_KEY}" ]]; then
        print_error "GOOGLE_API_KEY environment variable is not set"
        exit 1
    fi
    
    if [[ -z "${POSTGRES_PASSWORD}" ]]; then
        print_error "POSTGRES_PASSWORD environment variable is not set"
        exit 1
    fi
    
    if [[ -z "${JWT_SECRET_KEY}" ]]; then
        print_error "JWT_SECRET_KEY environment variable is not set"
        exit 1
    fi
    
    print_status "Environment configuration completed"
}


# Migrate database
migrate_db() {
    print_status "Running database migrations..."
    
    # Run alembic migrations
    docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm backend alembic upgrade head
    
    print_status "Database migrations completed"
}


# Rollback deployment
rollback() {
    print_warning "Rolling back deployment..."
    
    # Find the previous backup
    LATEST_BACKUP=$(ls -td /opt/${PROJECT_NAME}/backups/backup_* 2>/dev/null | head -n1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backups found to rollback to"
        exit 1
    fi
    
    print_status "Restoring from backup: $LATEST_BACKUP"
    cp -r "${LATEST_BACKUP}/data/" /opt/${PROJECT_NAME}/
    
    # Restart services
    docker-compose -f docker-compose.${ENVIRONMENT}.yml down
    docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d
    
    print_status "Rollback completed"
}


# Show deployment status
show_status() {
    print_status "Showing deployment status for ${ENVIRONMENT}..."
    
    docker-compose -f docker-compose.${ENVIRONMENT}.yml ps
    
    # Show resource usage
    docker stats --no-stream || true
}


# Main function
main() {
    ACTION=${1:-"deploy"}
    
    case $ACTION in
        "deploy")
            check_prerequisites
            configure_environment
            setup_ssl
            build_images
            run_tests
            migrate_db
            deploy
            ;;
        "health")
            check_health
            run_health_checks
            ;;
        "status")
            show_status
            ;;
        "rollback")
            rollback
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "test")
            check_prerequisites
            run_tests
            ;;
        *)
            echo "Usage: $0 {deploy|health|status|rollback|build|test}"
            echo "  deploy: Deploy the application (default action)"
            echo "  health: Check health of deployed services"
            echo "  status: Show status of deployed services"
            echo "  rollback: Rollback to previous deployment"
            echo "  build: Build Docker images only"
            echo "  test: Run all tests"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"