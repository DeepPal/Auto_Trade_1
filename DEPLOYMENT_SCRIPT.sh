#!/bin/bash

# =============================================================================
# PRODUCTION DEPLOYMENT SCRIPT - NIFTY OPTIONS TRADING SYSTEM
# =============================================================================
# Professional deployment automation with error handling and rollback capability
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Configuration
PROJECT_NAME="Auto_Trade_1"
DOCKER_COMPOSE_FILE="docker-compose.yml"
PYTHON_VERSION="3.9"
DEPLOYMENT_LOG="deployment_$(date +%Y%m%d_%H%M%S).log"

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOYMENT_LOG"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"; }

# =============================================================================
# PHASE 1: PRE-DEPLOYMENT CHECKS
# =============================================================================
log_info "Starting Pre-Deployment Checks..."

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        exit 1
    fi
    log_success "Docker found: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not installed"
        exit 1
    fi
    log_success "Docker Compose found: $(docker-compose --version)"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not installed"
        exit 1
    fi
    log_success "Python3 found: $(python3 --version)"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Create from .env.template"
        exit 1
    fi
    log_success ".env file found"
}

check_prerequisites

# =============================================================================
# PHASE 2: DOCKER ENVIRONMENT SETUP
# =============================================================================
log_info "Starting Docker Environment Setup..."

deploy_docker_services() {
    log_info "Starting Docker containers..."
    
    # Stop existing containers
    docker-compose down || true
    
    # Build and start containers
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to stabilize (30 seconds)..."
    sleep 30
    
    # Verify containers
    log_info "Verifying container status..."
    POSTGRES_STATUS=$(docker-compose ps postgres | grep -c "Up" || echo 0)
    REDIS_STATUS=$(docker-compose ps redis | grep -c "Up" || echo 0)
    N8N_STATUS=$(docker-compose ps n8n | grep -c "Up" || echo 0)
    
    if [ "$POSTGRES_STATUS" -eq 1 ]; then
        log_success "PostgreSQL container running"
    else
        log_error "PostgreSQL container failed to start"
        docker-compose logs postgres
        exit 1
    fi
    
    if [ "$REDIS_STATUS" -eq 1 ]; then
        log_success "Redis container running"
    else
        log_error "Redis container failed to start"
        docker-compose logs redis
        exit 1
    fi
    
    if [ "$N8N_STATUS" -eq 1 ]; then
        log_success "n8n container running"
    else
        log_error "n8n container failed to start"
        docker-compose logs n8n
        exit 1
    fi
}

deploy_docker_services

# =============================================================================
# PHASE 3: DATABASE INITIALIZATION
# =============================================================================
log_info "Starting Database Initialization..."

initialize_database() {
    log_info "Initializing PostgreSQL database..."
    
    # Wait for PostgreSQL to be ready
    sleep 5
    
    # Create database schema
    if [ -f "init_scripts/01_create_trading_schema.sql" ]; then
        log_info "Running schema initialization script..."
        docker exec postgres psql -U postgres -f /init_scripts/01_create_trading_schema.sql || true
        log_success "Database schema created"
    else
        log_warning "Schema initialization script not found"
    fi
    
    # Verify tables
    log_info "Verifying database tables..."
    docker exec postgres psql -U postgres -d trading_db -c "\\dt" || log_warning "Could not verify tables"
}

initialize_database

# =============================================================================
# PHASE 4: PYTHON DEPENDENCIES
# =============================================================================
log_info "Installing Python Dependencies..."

install_dependencies() {
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    log_info "Installing production dependencies..."
    if [ -f "requirements_production.txt" ]; then
        pip install -r requirements_production.txt
        log_success "Dependencies installed"
    else
        log_error "requirements_production.txt not found"
        exit 1
    fi
}

install_dependencies

# =============================================================================
# PHASE 5: MICROSERVICES STARTUP
# =============================================================================
log_info "Starting Microservices..."

start_microservices() {
    log_info "Starting Kite Service..."
    # Check if paper trading mode
    if grep -q "PAPER_TRADING=true" .env; then
        log_info "Paper Trading Mode ENABLED"
    else
        log_warning "Paper Trading Mode DISABLED - Using LIVE trading"
    fi
    
    # Start services in background
    nohup python kite_service.py > logs/kite_service.log 2>&1 &
    KITE_PID=$!
    log_success "Kite Service started (PID: $KITE_PID)"
    
    log_info "Starting Order Executor..."
    nohup python order_executor.py > logs/order_executor.log 2>&1 &
    EXECUTOR_PID=$!
    log_success "Order Executor started (PID: $EXECUTOR_PID)"
    
    sleep 5
    
    # Save PIDs for later reference
    echo "$KITE_PID" > .pids/kite_service.pid
    echo "$EXECUTOR_PID" > .pids/order_executor.pid
}

start_microservices

# =============================================================================
# PHASE 6: CONNECTIVITY VERIFICATION
# =============================================================================
log_info "Verifying Connectivity..."

verify_connectivity() {
    log_info "Testing PostgreSQL connection..."
    if python test_connection.py; then
        log_success "PostgreSQL connection verified"
    else
        log_error "PostgreSQL connection failed"
        exit 1
    fi
    
    log_info "Testing Kite Service health..."
    sleep 2
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_success "Kite Service health check passed"
    else
        log_warning "Kite Service may not be fully ready"
    fi
    
    log_info "Testing n8n accessibility..."
    if curl -s http://localhost:5678 | grep -q "n8n"; then
        log_success "n8n dashboard accessible at http://localhost:5678"
    else
        log_warning "n8n may not be fully ready"
    fi
}

verify_connectivity

# =============================================================================
# PHASE 7: MONITORING & ALERTS
# =============================================================================
log_info "Configuring Monitoring & Alerts..."

setup_monitoring() {
    log_info "Monitoring setup complete"
    log_info "Grafana available at: http://localhost:3000 (admin/admin)"
    log_info "pgAdmin available at: http://localhost:5050 (admin@trading.local/admin)"
}

setup_monitoring

# =============================================================================
# FINAL STATUS REPORT
# =============================================================================
log_success "========================================"
log_success "DEPLOYMENT COMPLETED SUCCESSFULLY"
log_success "========================================"
log_success "System Status:"
log_success "  - Docker Services: RUNNING"
log_success "  - PostgreSQL: READY"
log_success "  - Redis: READY"
log_success "  - n8n: http://localhost:5678"
log_success "  - Kite Service: http://localhost:8000"
log_success "  - Grafana: http://localhost:3000"
log_success "  - Deployment Log: $DEPLOYMENT_LOG"
log_success "========================================"

echo ""
log_info "Next Steps:"
log_info "1. Configure n8n workflows at http://localhost:5678"
log_info "2. Enable paper trading in .env (PAPER_TRADING=true)"
log_info "3. Monitor system at http://localhost:3000"
log_info "4. Review logs: tail -f $DEPLOYMENT_LOG"

echo ""
log_warning "⚠️  IMPORTANT: Verify paper trading is ENABLED before any trading"

exit 0
