# 🚀 n8n Workflows - Quick Setup Guide
## Configure 5 Workflows in 30 Minutes

---

## **FASTEST WAY TO SET UP (2 OPTIONS)**

### **Option 1: Manual Configuration (25 Minutes)**
If you want to understand each step, follow this guide.

### **Option 2: Import Pre-Built JSONs (5 Minutes)**
Contact the development team for pre-built workflow JSON files that can be imported directly.

---

## **WORKFLOW 1: Daily Token Refresh**

### Time to Setup: 3 minutes

**Purpose**: Refresh Zerodha Kite access token at 9:15 AM IST every trading day

**Steps:**
1. In n8n, click "Create workflow"
2. Name it: `01-Daily-Token-Refresh`
3. Click the center + icon to add first step
4. Search for and select: **"Schedule Trigger"** (On a schedule)
5. Configure trigger:
   - Trigger Interval: **Days**
   - Days Between Triggers: **1**
   - Trigger at Hour: **9am**
   - Trigger at Minute: **15**
   - Add Rule (optional but recommended for weekdays only)
6. Click the + icon to add next node
7. Search for and select: **"HTTP Request"**
8. Configure HTTP node:
   - Method: **POST**
   - URL: `http://localhost:8000/token`
   - Headers: Add `Content-Type: application/json`
9. Click the + icon to add final node
10. Search for and select: **"Telegram"**
11. Configure Telegram:
    - Message: `✅ Kite token refreshed at {{ now }}`
12. Activate the workflow (toggle in top right)

---

## **WORKFLOW 2: Signal Generation Engine**

### Time to Setup: 5 minutes

**Purpose**: Generate NIFTY trading signals every 1 minute during market hours

**Steps:**
1. Create new workflow: `02-Signal-Generation-Engine`
2. Add trigger: **Schedule Trigger**
   - Trigger Interval: **Minutes**
   - Minutes Between Triggers: **1**
   - Add Rule: Only run between 09:15 and 15:29
3. Add HTTP node #1 - Fetch Market Data:
   - POST `http://localhost:8000/market-data/NIFTY50`
4. Add HTTP node #2 - Get Options Chain:
   - POST `http://localhost:8000/options-chain`
5. Add HTTP node #3 - Generate Signals:
   - POST `http://localhost:8001/generate-signals`
   - Body: Include data from previous nodes
6. Add IF node:
   - Condition: `signal_score >= 70`
7. Add PostgreSQL node - True path (signal received):
   - Query: `INSERT INTO signals (symbol, score, entry, sl, target, timestamp) VALUES (...)`
8. Add Telegram node - Notify on signal:
   - Message: `📊 SIGNAL: {{ symbol }} Score: {{ score }}`
9. Activate workflow

---

## **WORKFLOW 3: Order Execution**

### Time to Setup: 5 minutes

**Purpose**: Execute trades when signals meet criteria

**Steps:**
1. Create new workflow: `03-Order-Execution`
2. Add trigger: **Webhook**
   - Copy webhook URL (you'll use this to call this workflow)
3. Add HTTP node - Check Risk Limits:
   - POST `http://localhost:8001/check-risk-limits`
4. Add IF node:
   - Condition: `allowed == true`
5. Add HTTP node (True path) - Calculate Position Size:
   - POST `http://localhost:8001/calculate-position-size`
6. Add HTTP node - Place Order:
   - POST `http://localhost:8001/place-order`
   - Body: Include all position details
7. Add PostgreSQL node:
   - Log order to database
8. Add Telegram node (Success):
   - Message: `🟢 ORDER PLACED: {{ symbol }} | Entry: {{ price }}`
9. Add Telegram node (False path - Risk Check Failed):
   - Message: `🔴 ORDER REJECTED: Risk limit breached`
10. Activate workflow

---

## **WORKFLOW 4: Position Monitoring**

### Time to Setup: 5 minutes

**Purpose**: Monitor open positions every 5 minutes and manage exits

**Steps:**
1. Create new workflow: `04-Position-Monitoring`
2. Add trigger: **Schedule Trigger**
   - Minutes Between Triggers: **5**
   - Time window: 09:15 - 15:30
3. Add PostgreSQL node - Get Open Positions:
   - Query: `SELECT * FROM positions WHERE status = 'OPEN'`
4. Add HTTP node - Fetch Current Prices:
   - POST `http://localhost:8000/market-data/...`
5. Add Loop node to iterate through positions
6. Inside loop - Add IF node for Stop Loss:
   - Condition: `current_price <= stop_loss_price`
7. Add HTTP node (Stop Loss triggered):
   - POST `http://localhost:8001/execute-stop-loss`
8. Add another IF node for Take Profit:
   - Condition: `current_price >= target_price`
9. Add HTTP node (Profit Target triggered):
   - POST `http://localhost:8001/execute-take-profit`
10. Add Telegram node - Send Update:
    - Message: `📈 POSITION UPDATE: {{ symbol }} P&L: {{ pnl }}`
11. Activate workflow

---

## **WORKFLOW 5: Market Close Square-Off**

### Time to Setup: 4 minutes

**Purpose**: Auto square-off all positions before 3:30 PM market close

**Steps:**
1. Create new workflow: `05-Market-Close-Square-Off`
2. Add trigger: **Schedule Trigger**
   - Trigger at Hour: **3pm**
   - Trigger at Minute: **29**
   - Weekdays only
3. Add PostgreSQL node - Get All Open Positions:
   - Query: `SELECT * FROM positions WHERE status = 'OPEN'`
4. Add IF node:
   - Condition: `count > 0`
5. Add Loop node (True path) to iterate through positions
6. Inside loop - Add HTTP node - Place Exit Order:
   - POST `http://localhost:8001/place-order`
   - Exit order configuration (reverse of entry)
7. Add PostgreSQL node - Update Position Status:
   - Query: `UPDATE positions SET status='CLOSED', exit_time=NOW()`
8. Outside loop - Add HTTP node - Calculate Daily Summary:
   - Query database for daily P&L
9. Add Telegram node (Positions existed):
   - Message: `🔴 MARKET CLOSE: Squared off {{ count }} positions | Daily P&L: {{ pnl }}`
10. Add Telegram node (No positions):
    - Message: `✅ Market close: No open positions`
11. Activate workflow

---

## **CONFIGURE CREDENTIALS (Required for All Workflows)**

1. Go to n8n Settings → Credentials
2. Create HTTP Credential:
   - Name: `Kite-Service`
   - Base URL: `http://localhost:8000`
3. Create PostgreSQL Credential:
   - Host: `postgres`
   - Port: `5432`
   - Database: `trading_db`
   - User: `postgres`
   - Password: (from .env)
4. Create Telegram Credential:
   - Bot Token: (from .env)
   - Chat ID: (from .env)

---

## **ACTIVATE ALL WORKFLOWS**

1. Go back to Overview
2. Verify all 5 workflows are visible
3. Each workflow should have a green toggle in top right
4. Test each workflow manually using "Execute workflow" button

---

## **VERIFICATION CHECKLIST**

- [ ] Workflow 1 runs at 9:15 AM every day
- [ ] Workflow 2 runs every minute (9:15-15:29 only)
- [ ] Workflow 3 can be triggered via webhook
- [ ] Workflow 4 runs every 5 minutes (9:15-15:30 only)
- [ ] Workflow 5 runs at 3:29 PM every trading day
- [ ] All Telegram alerts received successfully
- [ ] PostgreSQL logging working correctly
- [ ] No errors in workflow executions

---

## **TROUBLESHOOTING**

**Workflow not triggering:**
- Check n8n logs: `docker-compose logs n8n`
- Verify credentials are set correctly
- Restart n8n: `docker-compose restart n8n`

**Telegram not sending messages:**
- Verify bot token and chat ID in credentials
- Test Telegram node manually
- Check network connectivity

**HTTP requests failing:**
- Verify microservices are running: `curl http://localhost:8000/health`
- Check service logs: `tail -f logs/kite_service.log`
- Verify URLs are correct (localhost:8000 and localhost:8001)

**Database errors:**
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check credentials: `docker exec postgres psql -U postgres -d trading_db`
- Review n8n error messages for SQL syntax issues

---

## **NEXT STEPS AFTER SETUP**

1. Run all workflows for 1 day in paper trading mode
2. Verify all logs and alert messages
3. Check database for trade records
4. Monitor Grafana dashboard
5. Once verified, system is ready for paper trading

---

**Setup Time**: 25 minutes for complete manual configuration
**Activation Time**: 5 minutes to test and activate all workflows
**Total Time to Live**: ~30 minutes

Once complete, your NIFTY options trading system will be fully automated!
