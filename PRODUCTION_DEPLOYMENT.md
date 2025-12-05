# 🚀 Production Deployment Guide - NIFTY Options Trading System

## Overview

This document provides step-by-step instructions for deploying India's production-grade options trading system.

## ✅ What Has Been Implemented

### 1. **Microservices (Production-Grade)**
- **kite_service.py**: Zerodha Kite authentication, market data, options chain, Greeks calculation
- **order_executor.py**: Order placement, risk management (₹20k daily limit, max 3 trades, 4 positions), Kelly Criterion sizing
- **nifty_strategy.py**: NIFTY strategy engine with ATM Call, Iron Condor, Short Strangle signals

### 2. **Risk Management (ENFORCED)**
- Daily loss limit: ₹20,000 (hard circuit breaker)
- Max trades per day: 3
- Max open positions: 4
- Stop loss: 40% of entry price
- Profit target: 40% of entry price
- Position sizing: Kelly Criterion based
- Auto square-off: 3:29 PM IST (before market close)

### 3. **Infrastructure**
- Docker containerization (all services)
- PostgreSQL for trade history and risk tracking
- Redis for caching and session management
- n8n for workflow automation
- Telegram notifications (real-time alerts)

## 🔧 Deployment Steps

### Step 1: Verify Prerequisites

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version  # Should be 3.9+

# Verify .env file exists
ls -la .env
```

### Step 2: Environment Configuration

```bash
# Create .env file (NEVER commit this)
cp .env.template .env

# Edit .env with your credentials:
# KITE_API_KEY=64f9f934-7e44-4438-8c61-3f937e7bd846
# KITE_API_SECRET=2190ea9f-6c3b-4ef4-869a-33b0bf7321e1
# KITE_USER_ID=WNZ960
# KITE_PASSWORD=Deep4321@
# PAPER_TRADING=true  # Enable paper trading initially
# TELEGRAM_BOT_TOKEN=your_bot_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### Step 3: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install production dependencies
pip install -r requirements_production.txt
```

### Step 4: Start Docker Services

```bash
# Navigate to project directory
cd Auto_Trade_1

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                 STATUS
# postgres             Up
# redis                Up
# n8n                  Up
# pgAdmin              Up
# Grafana              Up
```

### Step 5: Verify Connectivity

```bash
# Test database connection
python test_connection.py

# Test Kite authentication
curl http://localhost:8000/token

# Access n8n dashboard
# http://localhost:5678 (admin/changeme)
```

### Step 6: Database Initialization

```bash
# Run migration scripts
docker exec postgres psql -U postgres -d trading_db -f init_scripts/01_create_trading_schema.sql

# Verify tables created
docker exec postgres psql -U postgres -d trading_db -c "\\dt"
```

### Step 7: Deploy Microservices

```bash
# Start Kite service
python kite_service.py &

# Start order executor as background service
python order_executor.py &

# Verify services are running
curl http://localhost:8000/health
```

### Step 8: Configure n8n Workflows

1. Open n8n: http://localhost:5678
2. Create 5 workflows:
   - **Workflow 1**: Daily token refresh (9:15 AM IST trigger)
   - **Workflow 2**: Signal generation (every 1 minute during market hours)
   - **Workflow 3**: Order execution (triggered by signals > 70 score)
   - **Workflow 4**: Position monitoring (every 5 minutes)
   - **Workflow 5**: Market close square-off (3:29 PM IST trigger)

## 📊 Paper Trading Mode (30 Days Minimum)

### Step 1: Enable Paper Trading
```bash
# Edit .env
PAPER_TRADING=true
```

### Step 2: Run Simulations
```bash
# Start automated trading in paper mode
python -m pytest tests/paper_trading_test.py -v

# Monitor trades in real-time
curl http://localhost:8000/positions
```

### Step 3: Monitor Performance
- View P&L in Grafana: http://localhost:3000
- Check trade history in pgAdmin: http://localhost:5050
- Monitor logs: `docker-compose logs -f`

### Success Criteria for Paper Trading
- Minimum 20 completed trades
- Positive Sharpe ratio
- Drawdown < 15%
- Win rate > 45%
- No circuit breaker violations

## 🔴 Going Live (After Paper Trading Success)

### Step 1: Risk Management Review
```bash
# Verify all risk constraints are in code
grep -r "MAX_DAILY_LOSS" .
grep -r "MAX_TRADES_PER_DAY" .
grep -r "circuit_breaker" .
```

### Step 2: Disable Paper Trading
```bash
# Edit .env
PAPER_TRADING=false
```

### Step 3: Deploy to Production
```bash
# Push code to GitHub
git add .
git commit -m "Production deployment"
git push origin main

# Deploy via Docker
docker-compose -f docker-compose.prod.yml up -d
```

### Step 4: Monitoring
- Real-time Telegram alerts enabled
- Database logging all trades
- Grafana dashboards active
- Health checks running every minute

## 🛠️ Troubleshooting

### PostgreSQL Connection Error
```bash
# Check database status
docker-compose logs postgres

# Reset database
docker-compose down postgres
docker volume rm auto_trade_1_postgres_data
docker-compose up postgres -d
```

### Kite Authentication Failed
```bash
# Verify credentials in .env
echo $KITE_USER_ID
echo $KITE_API_KEY

# Test manually
python -c "from kiteconnect import KiteConnect; kite = KiteConnect(api_key='YOUR_KEY')"
```

### n8n Workflow Not Triggering
```bash
# Check n8n logs
docker-compose logs n8n

# Restart n8n
docker-compose restart n8n
```

## 📈 Performance Monitoring

### Grafana Dashboard Setup
1. Open http://localhost:3000
2. Add PostgreSQL data source: `postgres:5432`
3. Import dashboards:
   - Trading Performance (P&L, Sharpe, Drawdown)
   - Risk Metrics (Daily Loss, Trade Count, Open Positions)
   - System Health (CPU, Memory, API Response Times)

### Key Metrics to Monitor
- **Daily P&L**: Should stay > -₹20,000
- **Trade Count**: Should not exceed 3/day
- **Win Rate**: Target > 50%
- **Sharpe Ratio**: Target > 1.5
- **Max Drawdown**: Should not exceed 15%

## 🚨 Emergency Stop

```bash
# Immediately stop all trading
docker-compose stop

# Manual square-off of all positions
python emergency_square_off.py

# Review all open positions
curl http://localhost:8000/positions
```

## 📋 Daily Checklist

- [ ] Check Telegram alerts for overnight issues
- [ ] Verify PostgreSQL and Redis are running
- [ ] Review previous day's P&L
- [ ] Check circuit breaker status
- [ ] Monitor live trades every 30 minutes
- [ ] Verify market close square-off executed
- [ ] Review Grafana for anomalies

## 🔐 Security Checklist

- [ ] .env file is NOT in git
- [ ] Kite API credentials rotated every 3 months
- [ ] Database backups enabled
- [ ] SSL certificates installed
- [ ] 2FA enabled on Zerodha account
- [ ] API rate limits respected
- [ ] Logs encrypted and archived

## Support & Documentation

- **README.md**: Project overview and quick start
- **TRADING_SETUP_GUIDE.md**: Complete trading strategy guide
- **n8n Documentation**: http://localhost:5678/docs
- **Kite API Docs**: https://kite.trade/docs/connect/v3/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**Remember**: This is a sophisticated trading system. Always test thoroughly in paper mode before going live. Options trading involves risk of total loss.
