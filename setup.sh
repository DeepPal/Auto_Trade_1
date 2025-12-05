#!/bin/bash

# Trading Setup Installation Script
# For personal options trading with Zerodha + n8n + Windsurf

echo "======================================"
echo "Options Trading Setup Installer"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisite() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

echo "Checking prerequisites..."
echo "------------------------"
check_prerequisite "docker"
DOCKER_OK=$?
check_prerequisite "docker-compose"
COMPOSE_OK=$?
check_prerequisite "python3"
PYTHON_OK=$?
check_prerequisite "pip"
PIP_OK=$?
echo ""

if [ $DOCKER_OK -ne 0 ] || [ $COMPOSE_OK -ne 0 ]; then
    echo -e "${RED}Docker and Docker Compose are required. Please install them first.${NC}"
    exit 1
fi

# Create necessary directories
echo "Creating directory structure..."
echo "------------------------------"
mkdir -p n8n_data n8n_workflows backups
mkdir -p postgres_data redis_data
mkdir -p grafana_data grafana/dashboards grafana/datasources
mkdir -p pgadmin_data
mkdir -p logs scripts/indicators scripts/strategies
mkdir -p init_scripts
echo -e "${GREEN}✓${NC} Directories created"
echo ""

# Copy environment file
if [ ! -f .env ]; then
    echo "Setting up environment file..."
    cp .env.template .env
    echo -e "${YELLOW}⚠${NC} Please edit .env file with your credentials"
    echo ""
fi

# Create database initialization script
echo "Creating database schema..."
cat > init_scripts/01_create_trading_schema.sql << 'EOF'
-- Create trading database and schema
CREATE DATABASE trading_db;

\c trading_db;

CREATE SCHEMA IF NOT EXISTS trading;

-- Auth tokens table
CREATE TABLE IF NOT EXISTS trading.auth_tokens (
    id SERIAL PRIMARY KEY,
    token_type VARCHAR(50) UNIQUE NOT NULL,
    token_value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Strategies table
CREATE TABLE IF NOT EXISTS trading.strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 0,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Signals table
CREATE TABLE IF NOT EXISTS trading.signals (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES trading.strategies(id),
    symbol VARCHAR(50) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,
    strength DECIMAL(5,2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Orders table
CREATE TABLE IF NOT EXISTS trading.orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE,
    signal_id INTEGER REFERENCES trading.signals(id),
    symbol VARCHAR(50) NOT NULL,
    order_type VARCHAR(20),
    quantity INTEGER,
    price DECIMAL(10,2),
    status VARCHAR(20),
    placed_at TIMESTAMP,
    executed_at TIMESTAMP,
    metadata JSONB
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS trading.performance (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES trading.strategies(id),
    date DATE NOT NULL,
    pnl DECIMAL(10,2),
    win_rate DECIMAL(5,2),
    sharpe_ratio DECIMAL(5,2),
    max_drawdown DECIMAL(10,2),
    trades_count INTEGER,
    metadata JSONB,
    UNIQUE(strategy_id, date)
);

-- Create indexes
CREATE INDEX idx_signals_created_at ON trading.signals(created_at DESC);
CREATE INDEX idx_orders_status ON trading.orders(status);
CREATE INDEX idx_orders_symbol ON trading.orders(symbol);
CREATE INDEX idx_performance_date ON trading.performance(date DESC);

-- Insert default strategies
INSERT INTO trading.strategies (name, enabled, config) VALUES 
('iron_condor', false, '{"max_loss": 5000, "target_profit": 2000}'),
('short_strangle', false, '{"delta_target": 0.30, "days_to_expiry": 7}'),
('calendar_spread', false, '{"strike_selection": "ATM", "hedge_ratio": 1}');
EOF
echo -e "${GREEN}✓${NC} Database schema created"
echo ""

# Install Python dependencies
if [ $PYTHON_OK -eq 0 ] && [ $PIP_OK -eq 0 ]; then
    echo "Installing Python dependencies..."
    echo "--------------------------------"
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Python dependencies installed"
    else
        echo -e "${YELLOW}⚠${NC} Some Python dependencies failed to install"
    fi
    echo ""
fi

# Start Docker containers
echo "Starting Docker containers..."
echo "-----------------------------"
docker-compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Docker containers started"
else
    echo -e "${RED}✗${NC} Failed to start Docker containers"
    exit 1
fi
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service status..."
echo "-------------------------"
docker-compose ps
echo ""

# Display access URLs
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Access your services at:"
echo "------------------------"
echo "n8n:       http://localhost:5678"
echo "pgAdmin:   http://localhost:5050"
echo "Grafana:   http://localhost:3000"
echo "Redis:     localhost:6379"
echo "PostgreSQL: localhost:5432"
echo ""
echo "Default Credentials:"
echo "-------------------"
echo "n8n:      admin / changeme"
echo "pgAdmin:  admin@trading.local / admin"
echo "Grafana:  admin / admin"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Edit .env file with your Zerodha API credentials"
echo "2. Import n8n workflows from n8n_workflows/ directory"
echo "3. Configure MCP in Windsurf using the mcp_config.json"
echo "4. Run test_connection.py to verify setup"
echo "5. Start with paper trading for at least 30 days"
echo ""
echo -e "${GREEN}Happy Trading! Remember: Always manage your risk.${NC}"
