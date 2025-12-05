# 🔄 n8n Workflows Setup Guide
## Professional Configuration for NIFTY Options Trading

---

## **Workflow 1: Daily Token Refresh (9:15 AM IST)**

### Purpose
Refresh Zerodha Kite access token at market open every trading day.

### Configuration
- **Trigger**: Cron job at 09:15 AM IST, Monday-Friday
- **Endpoint**: POST http://localhost:8000/token
- **Action**: Refresh access token and cache in Redis
- **Notification**: Send Telegram confirmation
- **Error Handling**: Retry 3 times with 30-second delay

---

## **Workflow 2: Signal Generation (Every 1 Minute)**

### Purpose
Generate NIFTY trading signals based on technical analysis.

### Flow
1. Fetch market data (NIFTY50 price)
2. Retrieve options chain (ATM +/- 100 points)
3. Calculate technical indicators (RSI, MACD)
4. Calculate Greeks (Delta, Gamma, Theta, Vega)
5. Generate signals (threshold >= 70)
6. Store signals in database

### Conditions
- Active only 09:15 AM - 15:29 PM IST
- Every 1 minute execution
- Only weekdays (Mon-Fri)

---

## **Workflow 3: Order Execution (Webhook)**

### Purpose
Execute trades when high-confidence signals generated.

### Pre-Execution Checks
- Risk limits validation (daily loss, trade count, positions)
- Market hours verification
- Paper trading mode check
- Circuit breaker status

### Execution Steps
1. Calculate position size (Kelly Criterion)
2. Place order with Zerodha
3. Log to database
4. Send Telegram alert
5. Track position

---

## **Workflow 4: Position Monitoring (Every 5 Minutes)**

### Purpose
Monitor open positions and manage exits.

### Monitoring
- Current price vs entry
- Unrealized P&L
- Greeks changes (Theta decay)
- Stop loss distance
- Profit target distance

### Auto Actions
- Trigger stop loss if price breaches
- Trigger take profit if target reached
- Send updates every 5 minutes

---

## **Workflow 5: Market Close Square-Off (3:29 PM IST)**

### Purpose
Auto square-off all open positions before 3:30 PM market close.

### Actions
1. Fetch all open positions
2. Place exit orders at market price
3. Update position status to CLOSED
4. Calculate daily P&L
5. Send closing report
6. Archive trades for audit

---

## **Setup Instructions**

### Credentials to Create
1. Kite HTTP Service (http://localhost:8000)
2. PostgreSQL Database (postgres:5432)
3. Redis Cache (redis:6379)
4. Telegram Bot API

### Import & Activate
1. Open n8n: http://localhost:5678
2. Create → Import Workflow
3. Configure each credential
4. Test execution
5. Activate all 5 workflows

### Verify All Running
```
- Workflow 1: Daily token at 09:15 AM IST
- Workflow 2: Signals every 1 minute
- Workflow 3: Ready for webhook triggers
- Workflow 4: Monitoring every 5 minutes
- Workflow 5: Close-out at 3:29 PM IST
```

---

**Status**: Production-ready configuration guide
