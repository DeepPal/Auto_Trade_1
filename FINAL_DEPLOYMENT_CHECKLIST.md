# ✅ FINAL DEPLOYMENT CHECKLIST - NIFTY OPTIONS TRADING SYSTEM
## Production-Ready Verification

---

## **PHASE 1: PRE-DEPLOYMENT (Before Running Script)**

### Infrastructure Requirements
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 1.29+)
- [ ] Python 3.9+ installed
- [ ] Minimum 4GB RAM available
- [ ] Minimum 20GB disk space free
- [ ] Network connectivity verified

### Credentials & Configuration
- [ ] .env file created (copied from .env.template)
- [ ] Zerodha credentials configured:
  - [ ] KITE_API_KEY set
  - [ ] KITE_API_SECRET set
  - [ ] KITE_USER_ID set
  - [ ] KITE_PASSWORD set
- [ ] PAPER_TRADING=true (for initial testing)
- [ ] Telegram Bot Token configured
- [ ] Telegram Chat ID configured
- [ ] Database password set (POSTGRES_PASSWORD)

### Repository Status
- [ ] Git repository cloned
- [ ] All microservices files present:
  - [ ] kite_service.py
  - [ ] order_executor.py
  - [ ] nifty_strategy.py
- [ ] Docker Compose file exists
- [ ] requirements_production.txt present
- [ ] Database init scripts in init_scripts/ folder

---

## **PHASE 2: RUNNING DEPLOYMENT SCRIPT**

### Script Execution
```bash
chmod +x DEPLOYMENT_SCRIPT.sh
./DEPLOYMENT_SCRIPT.sh
```

### Expected Output During Execution
- [ ] Docker prerequisites check: PASS
- [ ] Docker containers started: PASS
- [ ] PostgreSQL container running: PASS
- [ ] Redis container running: PASS
- [ ] n8n container running: PASS
- [ ] Database initialization: PASS
- [ ] Python dependencies installed: PASS
- [ ] Kite Service started: PASS
- [ ] Order Executor started: PASS
- [ ] PostgreSQL connection verified: PASS
- [ ] Kite Service health check: PASS
- [ ] n8n dashboard accessible: PASS

---

## **PHASE 3: POST-DEPLOYMENT VERIFICATION**

### Service Verification
- [ ] **PostgreSQL** (Port 5432)
  ```bash
  docker-compose ps | grep postgres
  ```
  Status: UP

- [ ] **Redis** (Port 6379)
  ```bash
  docker-compose ps | grep redis
  ```
  Status: UP

- [ ] **n8n** (Port 5678)
  - [ ] Open http://localhost:5678
  - [ ] Login: admin/changeme
  - [ ] Dashboard loads successfully

- [ ] **Kite Service** (Port 8000)
  - [ ] Test endpoint: curl http://localhost:8000/health
  - [ ] Expected response: {"status": "healthy"}

- [ ] **Grafana** (Port 3000)
  - [ ] Open http://localhost:3000
  - [ ] Login: admin/admin
  - [ ] Dashboard accessible

- [ ] **pgAdmin** (Port 5050)
  - [ ] Open http://localhost:5050
  - [ ] Login: admin@trading.local/admin
  - [ ] Can connect to trading_db

### Database Verification
- [ ] Connect to PostgreSQL database
  ```bash
  docker exec postgres psql -U postgres -d trading_db -c "\\dt"
  ```
- [ ] Verify tables exist:
  - [ ] trades
  - [ ] positions
  - [ ] signals
  - [ ] account_status

### Microservices Verification
- [ ] Kite Service logs:
  ```bash
  tail -f logs/kite_service.log
  ```
  - [ ] No fatal errors
  - [ ] Connection initialized

- [ ] Order Executor logs:
  ```bash
  tail -f logs/order_executor.log
  ```
  - [ ] No fatal errors
  - [ ] Risk manager initialized

---

## **PHASE 4: RISK MANAGEMENT VERIFICATION**

### Constraint Validation
- [ ] Daily Loss Limit
  - [ ] Configuration: MAX_DAILY_LOSS = ₹20,000
  - [ ] Code verification: grep -r "MAX_DAILY_LOSS" .
  - [ ] Status: HARDCODED (immutable)

- [ ] Max Trades Per Day
  - [ ] Configuration: MAX_TRADES_PER_DAY = 3
  - [ ] Code verification: grep -r "MAX_TRADES_PER_DAY" .
  - [ ] Status: HARDCODED (immutable)

- [ ] Max Open Positions
  - [ ] Configuration: MAX_OPEN_POSITIONS = 4
  - [ ] Code verification: grep -r "MAX_OPEN_POSITIONS" .
  - [ ] Status: HARDCODED (immutable)

- [ ] Stop Loss / Profit Target
  - [ ] Configuration: SL = 40%, Target = 40%
  - [ ] Code verification: grep -r "STOP_LOSS\|PROFIT_TARGET" .
  - [ ] Status: HARDCODED (immutable)

- [ ] Market Hours Enforcement
  - [ ] Configuration: 09:15 AM - 3:30 PM IST
  - [ ] Code verification: grep -r "MARKET_OPEN\|MARKET_CLOSE" .
  - [ ] Status: ENFORCED

---

## **PHASE 5: n8n WORKFLOW SETUP**

### Workflow 1: Token Refresh
- [ ] Open n8n dashboard: http://localhost:5678
- [ ] Create new workflow
- [ ] Name: "Daily Token Refresh"
- [ ] Configure trigger: Cron 09:15 AM IST
- [ ] Test execution
- [ ] Activate workflow

### Workflow 2: Signal Generation
- [ ] Create new workflow
- [ ] Name: "Signal Generation Engine"
- [ ] Configure trigger: Every 1 minute
- [ ] Configure time window: 09:15-15:29 IST
- [ ] Test execution
- [ ] Activate workflow

### Workflow 3: Order Execution
- [ ] Create new workflow
- [ ] Name: "Order Execution"
- [ ] Configure trigger: Webhook
- [ ] Test execution
- [ ] Activate workflow

### Workflow 4: Position Monitoring
- [ ] Create new workflow
- [ ] Name: "Position Monitoring"
- [ ] Configure trigger: Every 5 minutes
- [ ] Test execution
- [ ] Activate workflow

### Workflow 5: Market Close
- [ ] Create new workflow
- [ ] Name: "Market Close Square-Off"
- [ ] Configure trigger: Cron 15:29 IST
- [ ] Test execution
- [ ] Activate workflow

---

## **PHASE 6: PAPER TRADING MODE**

### Activation
- [ ] Verify PAPER_TRADING=true in .env
- [ ] Restart services: `docker-compose restart`
- [ ] Verify in logs: grep "Paper Trading" logs/*.log

### Testing
- [ ] Generate test signals
- [ ] Verify signals stored in database
- [ ] Verify no actual orders placed
- [ ] Monitor P&L simulation
- [ ] Run for minimum 30 days

### Success Criteria
- [ ] Minimum 20 completed simulated trades
- [ ] Positive Sharpe ratio
- [ ] Drawdown < 15%
- [ ] Win rate > 45%
- [ ] Zero circuit breaker violations
- [ ] All risk constraints enforced

---

## **PHASE 7: MONITORING SETUP**

### Grafana Dashboards
- [ ] Add PostgreSQL data source
- [ ] Import trading performance dashboard
- [ ] Verify metrics:
  - [ ] Daily P&L
  - [ ] Win Rate
  - [ ] Sharpe Ratio
  - [ ] Max Drawdown
  - [ ] Trade Count

### Telegram Alerts
- [ ] Verify token refresh alert received
- [ ] Verify signal generation alerts
- [ ] Verify order execution alerts
- [ ] Verify position monitoring alerts
- [ ] Verify market close alerts

---

## **PHASE 8: LIVE TRADING ACTIVATION (After 30-Day Paper Trading)**

### Go-Live Checklist
- [ ] Paper trading completed successfully
- [ ] All success criteria met
- [ ] Risk management thoroughly tested
- [ ] Team review and approval
- [ ] Backup and rollback procedures documented

### Activation Steps
- [ ] Set PAPER_TRADING=false in .env
- [ ] Restart all services: `docker-compose restart`
- [ ] Verify in logs: grep "Paper Trading" logs/*.log
- [ ] Confirm no PAPER_TRADING=true in output

### First Live Day
- [ ] Start with minimal capital
- [ ] Monitor every 5 minutes
- [ ] Have emergency stop procedure ready
- [ ] Review all trades at end of day
- [ ] Continue daily monitoring

---

## **TROUBLESHOOTING**

### Docker Issues
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f [service_name]

# Rebuild containers
docker-compose build --no-cache
```

### Database Issues
```bash
# Access database
docker exec postgres psql -U postgres

# Reset database
docker-compose down postgres
docker volume rm auto_trade_1_postgres_data
docker-compose up -d postgres
```

### Service Issues
```bash
# Check microservice logs
tail -f logs/kite_service.log
tail -f logs/order_executor.log

# Restart services
pkill -f kite_service.py
pkill -f order_executor.py
nohup python kite_service.py > logs/kite_service.log 2>&1 &
nohup python order_executor.py > logs/order_executor.log 2>&1 &
```

### Network Issues
```bash
# Test service connectivity
curl http://localhost:8000/health
curl http://localhost:5678
curl http://localhost:3000
```

---

## **EMERGENCY PROCEDURES**

### Immediate Stop
```bash
# Stop all trading
docker-compose stop

# Kill microservices
pkill -f kite_service.py
pkill -f order_executor.py

# Emergency square-off all positions
python emergency_square_off.py
```

### Rollback
```bash
# Revert to previous version
git checkout HEAD~1

# Restart with previous deployment
./DEPLOYMENT_SCRIPT.sh
```

---

## **FINAL VERIFICATION**

- [ ] All services running and healthy
- [ ] All risk constraints verified and hardcoded
- [ ] All workflows tested and activated
- [ ] Paper trading mode confirmed ENABLED
- [ ] Monitoring and alerts verified
- [ ] Emergency procedures documented
- [ ] Team trained and ready
- [ ] Documentation complete and accessible

---

## **DEPLOYMENT STATUS**

**Status**: ✅ PRODUCTION-READY

**Deployment Date**: [INSERT DATE]
**Deployed By**: [INSERT NAME]
**Reviewed By**: [INSERT NAME]
**Approved By**: [INSERT NAME]

---

**⚠️ CRITICAL REMINDERS:**
- Paper trading MUST be enabled before any market activity
- All risk constraints are immutable and hardcoded
- Maximum daily loss will trigger automatic circuit breaker at ₹20,000
- All positions auto-square-off before 3:30 PM market close
- Keep emergency stop procedures accessible at all times

**Last Updated**: December 6, 2025
**Version**: 1.0 - Production Release
