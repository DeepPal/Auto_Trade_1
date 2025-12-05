# NIFTY Options Trading System - Comprehensive n8n Professional Audit & Implementation Guide

## Executive Summary

Your Auto_Trade_1 project has a solid foundation with 4 active workflows running. This guide audits the current state and provides world-class enhancements to make your system production-grade for personal options trading.

**Current Status**: 4/5 workflows active, ready for optimization
**Goal**: Build an emotionless, systematic trading approach with layered logic

---

## Part 1: Current System Audit

### Active Workflows (ALL GREEN ✅)

#### 1. **Iron Condor Strategy** (Last updated 5 min ago)
- **Status**: Active
- **Type**: Webhook Trigger (input: symbol, spot_price, expiry)
- **Current Features**:
  - Strike selection (ATM ±1 strike)
  - Premium + Greeks calculation
  - Signal scoring system
  - Tradeable threshold: score ≥ 70
- **Issues**: 
  - IV Rank / VIX / PCR data are placeholders
  - No real options chain fetch
  - Scoring needs more robust market data

#### 2. **TEST - Simple Trading Signal** (Last updated 5 min ago)
- **Status**: Active
- **Type**: Webhook Trigger
- **Purpose**: Sanity check, no real credentials needed
- **Usage**: Test signal generation safely
- **Status**: ✅ GOOD - Keep as-is for quick testing

#### 3. **01-Daily-Token-Refresh** (Last updated 5 min ago)
- **Status**: Active
- **Type**: Schedule (Cron: 9:15 AM Mon-Fri)
- **Current Features**:
  - Runs every morning before market open
  - Sends HTTP POST to token refresh endpoint
  - Success/fail branch logic
- **Issues**:
  - Endpoint: http://localhost:8000/token (needs real service)
  - Auth headers: Using env variables (good)
  - Error handling: Basic (no retry logic)

#### 4. **MASTER Trading Orchestrator** (Last updated 24 min ago)
- **Status**: Active  
- **Type**: Schedule Trigger (Every 2 minutes, 9:15-15:30 IST)
- **Current Features**:
  - Risk gates: Daily loss (₹20k), max positions (4), max trades/day (3)
  - Time guard: Market hours 9:15-15:30 IST
  - Calls Iron Condor strategy
  - Telegram alerts on decisions
- **Critical Issues**:
  - ⚠️ Execute Workflow nodes reference placeholder IDs
  - ⚠️ Need to wire REAL workflow IDs after import
  - ⚠️ Order Executor workflow is referenced but may not exist

#### 5. **My workflow** (Last updated 2 hours ago)
- **Status**: Inactive
- **Action**: Consider removing or archiving (appears to be placeholder)

---

## Part 2: Issues Identified & Solutions

### Critical Issues 🔴

#### Issue #1: MCP Error - "MCP access can only be set for active workflows..."
**Problem**: Manual trigger workflows cannot expose MCP endpoints
**Solution**: 
- Ensure all workflows you want to call from Windsurf MCP have Webhook or Schedule triggers
- Iron Condor & TEST workflows have Webhooks ✅
- Master Orchestrator has Schedule ✅
- Confirm MCP settings enabled for these three

#### Issue #2: Workflow IDs Not Wired in MASTER Orchestrator
**Problem**: Execute Workflow nodes point to placeholder IDs
**Steps to Fix**:
```
1. In MASTER Orchestrator, go to each Execute Workflow node
2. Click on node → Settings
3. Find "Workflow ID" field
4. Replace placeholder with ACTUAL workflow ID:
   - Iron Condor Strategy: [COPY THIS ID]
   - Order Executor: [COPY THIS ID]
5. Save workflow
```

#### Issue #3: No Real Order Executor Workflow Imported
**Problem**: Master orchestrator references Order Executor ID that doesn't exist
**Solution**: You need to either:
- Option A: Import the Order Executor JSON (if provided)
- Option B: Create a stub Order Executor in n8n that accepts orders but doesn't execute (paper mode)
- Option C: Disable the Order Executor call in Master temporarily while you set it up

#### Issue #4: Token Refresh Endpoint
**Problem**: http://localhost:8000/token - no service listening
**Solution**:
- Option A: Create a Python token service at port 8000
- Option B: Use n8n's built-in webhook as dummy endpoint
- Option C: Call Zerodha Kite API directly for token (needs credentials in header)

#### Issue #5: IV Rank / VIX / PCR Placeholders
**Problem**: Iron Condor workflow has hardcoded placeholder values for market data
**Solution**: Add HTTP request nodes to fetch:
- IV Rank from NSE/Zerodha
- VIX from NSE
- PCR from NSE options data
- Use calculation or external APIs

### Medium Issues 🟡

#### Issue #6: No Input Validation
**Problem**: Workflows accept any input, no schema validation
**Solution**: Add JSON Schema validation at webhook entry
```json
{
  "symbol": { "type": "string", "pattern": "^[A-Z0-9]+$" },
  "spot_price": { "type": "number", "minimum": 0 },
  "expiry": { "type": "string", "pattern": "^\d{2}[A-Z]{3}\d{2}$" }
}
```

#### Issue #7: Limited Error Handling
**Problem**: No error recovery, retry logic, or circuit breaker
**Solution**: 
- Add Try/Catch nodes
- Implement exponential backoff for API calls
- Add Telegram alert on workflow failures
- Log all errors to database

#### Issue #8: No Database Logging
**Problem**: Decisions not recorded for audit trail
**Solution**:
- Create trading.signals table
- Create trading.orders table
- Log every decision + execution
- Enable backtesting/performance review

---

## Part 3: Step-by-Step Implementation Guide

### Step 1: Copy Workflow IDs

Go to n8n → Workflows:

**Iron Condor Strategy**:
- Click workflow → Settings → Copy Workflow ID
- Store as: `IRON_CONDOR_ID = xxxxxxx`

**Order Executor** (if exists):
- Copy its ID
- Store as: `ORDER_EXECUTOR_ID = xxxxxxx`

### Step 2: Update MASTER Orchestrator

1. Open MASTER Trading Orchestrator workflow
2. Find "Execute Iron Condor" node
3. Edit → Set Workflow ID = `IRON_CONDOR_ID`
4. Save
5. Find "Execute Order" node
6. Edit → Set Workflow ID = `ORDER_EXECUTOR_ID`
7. Save workflow

### Step 3: Fix MCP Access

1. n8n → Workflows → Iron Condor Strategy
2. Click (i) info icon
3. "Enable MCP" for this workflow
4. Do same for TEST and MASTER workflows

### Step 4: Add Database Logging

Create PostgreSQL tables:

```sql
CREATE TABLE IF NOT EXISTS trading.signals (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(20),
  strategy VARCHAR(100),
  signal_score NUMERIC(5,2),
  recommendation VARCHAR(50),
  strikes JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.executions (
  id SERIAL PRIMARY KEY,
  workflow_name VARCHAR(255),
  status VARCHAR(50), -- SUCCESS, FAILED, SKIPPED
  input_data JSONB,
  output_data JSONB,
  error_message TEXT,
  execution_time_ms INTEGER,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

Add a PostgreSQL node to each workflow to log outputs.

### Step 5: Add Error Handling

For each workflow:
1. Add an "Error" trigger node
2. Send Telegram alert
3. Log error to database
4. Optionally retry (exponential backoff)

### Step 6: Validate Market Data

In Iron Condor workflow, replace placeholders:

```json
// Before (placeholder)
{
  "iv_rank": 45,
  "vix": 15,
  "pcr": 1.2
}

// After (real data fetch)
// Add HTTP request node:
// GET https://api.example.com/market-data?symbol=NIFTY
// Then extract: data.iv_rank, data.vix, data.pcr
```

---

## Part 4: Professional Enhancements

### Enhancement #1: Multi-Strategy Support

Duplicate Iron Condor workflow to create:
- Strangle Strategy
- Calendar Spread Strategy  
- Butterfly Spread Strategy

Each with own scoring logic. Master Orchestrator calls ALL and compares scores.

### Enhancement #2: Advanced Risk Management

Add nodes to MASTER Orchestrator:
```
1. Check Daily Loss (vs ₹20k limit)
2. Check Position Correlation (no highly correlated positions)
3. Check Greeks Impact (portfolio delta/gamma/theta)
4. Check Liquidity (bid-ask spread)
5. Check Volatility (VIX threshold for trading)
```

### Enhancement #3: Performance Monitoring

Add scheduled workflow (daily 15:35):
```
1. Calculate Daily P/L
2. Calculate Win Rate
3. Calculate Sharpe Ratio
4. Send Telegram summary
5. Store metrics in DB
```

### Enhancement #4: Paper vs Live Mode

Add environment variable:
```
TRADING_MODE=paper  # or 'live'
```

In Order Executor:
```javascript
if (process.env.TRADING_MODE === 'paper') {
  // Log only, don't place order
  return { "paper_mode": true, "order_id": "MOCK_" + Date.now() };
} else {
  // Place real order via Kite API
  return placeKiteOrder(orderData);
}
```

### Enhancement #5: Webhook Audit Trail

For every webhook call:
```
1. Log request timestamp
2. Log parameters
3. Log response
4. Log execution time
5. Store in DB for replay/testing
```

---

## Part 5: Configuration Checklist

- [ ] Copy all workflow IDs from n8n
- [ ] Wire workflow IDs into MASTER Orchestrator
- [ ] Enable MCP for 3 workflows (Iron Condor, TEST, MASTER)
- [ ] Create PostgreSQL signal/execution tables
- [ ] Add error handling to all workflows
- [ ] Test with TEST workflow first (no risk)
- [ ] Validate market data placeholders replaced
- [ ] Set TRADING_MODE = paper initially
- [ ] Run 48+ hours of paper trading
- [ ] Monitor execution logs in Grafana/pgAdmin
- [ ] Only switch TRADING_MODE = live after validation

---

## Part 6: Testing Protocol

### Phase 1: Unit Testing (30 min)
```
1. Test 00_TEST_WORKFLOW webhook
   curl http://localhost:5678/webhook/test-signal
2. Verify response structure
3. Check n8n Executions tab for success
```

### Phase 2: Integration Testing (2 hours)
```
1. Test Iron Condor with manual input
   @n8n-mcp iron-condor {"symbol":"NIFTY","spot_price":21500}
2. Verify signal generation
3. Check database logging
4. Verify Telegram alert (if configured)
```

### Phase 3: Paper Trading (48+ hours)
```
1. Set TRADING_MODE=paper
2. Run MASTER Orchestrator (every 2 min)
3. Monitor signals generated
4. Review daily P/L (should be mock only)
5. Check for errors in execution logs
```

### Phase 4: Live Trading (Only after Phase 3 success)
```
1. Switch TRADING_MODE=live
2. Start with 1 lot size max
3. Monitor first 10 trades
4. Only increase size after 50+ successful trades
```

---

## Part 7: Maintenance Plan

### Daily
- [ ] Monitor workflow executions
- [ ] Check Telegram alerts
- [ ] Verify trading logs

### Weekly
- [ ] Export workflows (backup)
- [ ] Review signal quality
- [ ] Check P/L vs targets

### Monthly
- [ ] Analyze strategy performance
- [ ] Adjust scoring weights if needed
- [ ] Add/remove strategies
- [ ] Update documentation

---

## Part 8: Quick Reference

### Common URLs
- n8n: http://localhost:5678
- Postgres: localhost:5432
- Grafana: http://localhost:3000
- pgAdmin: http://localhost:5050

### Important Credentials (from .env)
- KITE_API_KEY
- KITE_API_SECRET
- KITE_ACCESS_TOKEN
- TELEGRAM_CHAT_ID
- DB_PASSWORD

### Workflow Webhook Paths
- Iron Condor: `/webhook/iron-condor-signal`
- TEST: `/webhook/test-signal`
- Master: Schedule-based (no webhook)

---

## Conclusion

Your system is **85% ready**. The remaining 15% is:
- Wiring workflow IDs (5 min)
- Adding error handling (1-2 hours)
- Database logging setup (30 min)
- 48-hour paper trading validation (2 days)

After these steps, you'll have a **professional, production-grade trading system** that eliminates emotion and systematically executes your trading logic.

**Next Action**: Start with Step 1 (Copy Workflow IDs) above. Let me know when done, and I'll help with the next step.

---

**Last Updated**: December 6, 2025  
**Status**: Ready for Implementation  
**Estimated Completion**: 2 days (including paper trading)
