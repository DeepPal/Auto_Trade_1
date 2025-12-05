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
