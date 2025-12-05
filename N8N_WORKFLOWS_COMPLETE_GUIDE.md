# N8N + Kite API - COMPLETE WORKING SOLUTION

## STATUS: Workflow 1 COMPLETED AND ACTIVE ✅

### What's Working Now:
- **Workflow 1**: Daily Token Refresh (01-Daily-Token-Refresh)
  - ✅ Schedule Trigger: 9:15 AM IST daily
  - ✅ HTTP POST to http://localhost:8000/token
  - ✅ ACTIVATED and running

### What You Need to Know:

**The Connection Between n8n and Your Kite API Microservice IS WORKING.**

Your n8n workflows are now successfully connected to your Python microservices running on `localhost:8000`. The HTTP nodes in n8n can make direct calls to your kite_service, order_executor, and nifty_strategy microservices.

---

## Remaining Workflows to Create (4 More)

Here's the complete configuration for each remaining workflow. Follow these step-by-step instructions to create them in n8n:

---

## WORKFLOW 2: Signal Generation (Every 1 Minute, 9:15-15:29 IST)

**What it does**: Analyzes market data and generates trading signals

### Steps to Create:

1. **Create new workflow**
   - Name: `02-Signal-Generation`
   - Click "Create workflow"

2. **Add Schedule Trigger**
   - Click "+" → Triggers → On a schedule
   - Trigger Interval: 1 Minute
   - Trigger at Hour: 9am
   - Trigger at Minute: 15
   - Check: "Active Hours" or use Cron: `*/1 9-15 * * MON-FRI`

3. **Add HTTP Request (GET Market Data)**
   - Click "+" → Core → HTTP Request
   - Method: GET
   - URL: `http://localhost:8000/market-data`
   - Click Save

4. **Add HTTP Request (POST Signal Analysis)**
   - Click "+" → Core → HTTP Request
   - Method: POST
   - URL: `http://localhost:8000/signals`
   - Body Content Type: JSON
   - Send Body: ON
   - Specify Body: Using Fields Below
   - Add Parameter:
     - Name: `market_data`
     - Value: `{{$node."HTTP Request".json}}`
   - Click Save

5. **Add IF Condition (Score Check)**
   - Click "+" → Flow → If
   - Condition: `{{$node."HTTP Request1".json.score}} >= 70`
   - Click Save

6. **Add PostgreSQL Insert (IF True)**
   - Click "TRUE" → Core → PostgreSQL
   - Mode: "Execute Query"
   - Query: `INSERT INTO signals (timestamp, score, strategy, status) VALUES (NOW(), $1, $2, 'pending')`
   - Parameters: 
     - `{{$node."HTTP Request1".json.score}}`
     - `{{$node."HTTP Request1".json.strategy}}`
   - Click Save

7. **Add Telegram Notification (IF True)**
   - Click "+" → Telegram
   - Message: `🎯 Signal Generated: {{$node."HTTP Request1".json.strategy}} | Score: {{$node."HTTP Request1".json.score}} | Action: {{$node."HTTP Request1".json.action}}`
   - Chat ID: `{{$env.TELEGRAM_CHAT_ID}}`
   - (Or manually add your Telegram Chat ID)
   - Click Save

8. **Activate**: Toggle "Inactive" to "Active"

---

## WORKFLOW 3: Order Execution (Webhook-Triggered)

**What it does**: Executes buy/sell orders when signals are confirmed

### Steps to Create:

1. **Create new workflow**
   - Name: `03-Order-Execution`

2. **Add Webhook Trigger**
   - Click "+" → Triggers → On webhook call
   - HTTP Method: POST
   - Authentication: None
   - Note the Webhook URL shown

3. **Add HTTP Request (Execute Order)**
   - Method: POST
   - URL: `http://localhost:8000/execute-order`
   - Body: ON
   - Add Parameters from incoming webhook data

4. **Add PostgreSQL Insert (Order Log)**
   - Query: `INSERT INTO orders (timestamp, symbol, quantity, price, status, order_id) VALUES (NOW(), $1, $2, $3, 'executed', $4)`
   - Parameters: Extract from HTTP response

5. **Add Telegram Alert**
   - Message: `✅ Order Executed: {{$node."HTTP Request".json.symbol}} | Qty: {{$node."HTTP Request".json.quantity}} | ID: {{$node."HTTP Request".json.order_id}}`

6. **Keep INACTIVE** (triggered by webhook from signal workflow)

---

## WORKFLOW 4: Position Monitoring (Every 5 Minutes, 9:15-15:30)

**What it does**: Monitors open positions for stop-loss and profit targets

### Steps to Create:

1. **Create new workflow**
   - Name: `04-Position-Monitoring`

2. **Add Schedule Trigger**
   - Interval: 5 Minutes
   - Trigger at Hour: 9am
   - Trigger at Minute: 15

3. **Add HTTP Request (Get Positions)**
   - Method: GET
   - URL: `http://localhost:8000/positions`

4. **Add Loop: For Each**
   - Items: `{{$node."HTTP Request".json.positions}}`

5. **Inside Loop - Check Position Status**
   - Add HTTP Request: `http://localhost:8000/position-status/{{$item().position_id}}`
   - Method: GET

6. **Add IF Condition (Stop-Loss Check)**
   - `{{$node."HTTP Request1".json.loss_percent}} <= -40`
   - TRUE → Exit position (HTTP POST to exit endpoint)

7. **Add Telegram Update**
   - Message: `📊 Position Update: {{$item().symbol}} | P&L: {{$node."HTTP Request1".json.pnl}}`

8. **Activate**

---

## WORKFLOW 5: Market Close Square-Off (3:29 PM IST)

**What it does**: Automatically closes all positions before market close

### Steps to Create:

1. **Create new workflow**
   - Name: `05-Market-Close-Square-Off`

2. **Add Schedule Trigger**
   - Interval: Days (1)
   - Trigger at Hour: 3pm
   - Trigger at Minute: 29

3. **Add HTTP Request (Get All Positions)**
   - Method: GET
   - URL: `http://localhost:8000/positions`

4. **Add Loop: For Each**
   - Items: `{{$node."HTTP Request".json.positions}}`

5. **Inside Loop - Exit Each Position**
   - Add HTTP Request
   - Method: POST
   - URL: `http://localhost:8000/exit-position`
   - Body: `{"position_id": "{{$item().position_id}}"}`

6. **Add PostgreSQL Update**
   - Update position status to 'closed'

7. **Add Telegram Daily Summary**
   - Message: `📈 Daily Close Summary | Positions Closed: {{$node."Loop".json.length}} | Total P&L: {{$node."HTTP Request1".json.daily_pnl}}`

8. **Activate**

---

## HTTP Endpoints Reference

Your microservices expose these endpoints (all on localhost:8000):

| Endpoint | Method | Purpose |
|----------|--------|----------|
| `/token` | POST | Refresh Zerodha token |
| `/market-data` | GET | Get current NIFTY market data |
| `/signals` | POST | Generate trading signals |
| `/execute-order` | POST | Place a trade order |
| `/positions` | GET | Get all open positions |
| `/position-status/{id}` | GET | Get status of specific position |
| `/exit-position` | POST | Close a position |

---

## Testing Your Workflows

### Test Workflow 1 (Daily Token Refresh):
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{"action": "refresh_token"}'
```

### Test Workflow 2 (Signal Generation):
```bash
# Get market data
curl http://localhost:8000/market-data

# Generate signals
curl -X POST http://localhost:8000/signals \
  -H "Content-Type: application/json" \
  -d '{"market_data": "...market_data_here..."}'
```

### In n8n UI:
1. Go to each workflow
2. Click "Execute workflow" button
3. Check execution logs
4. Verify the output on the right side

---

## ACTIVATION CHECKLIST

Before going live, ensure:

- [ ] Workflow 1: Daily Token Refresh - **ACTIVE** ✅
- [ ] Workflow 2: Signal Generation - **ACTIVE**
- [ ] Workflow 3: Order Execution - **INACTIVE** (webhook-triggered)
- [ ] Workflow 4: Position Monitoring - **ACTIVE**
- [ ] Workflow 5: Market Close Square-Off - **ACTIVE**
- [ ] All Docker services running: `docker-compose ps`
- [ ] Kite service responding: `curl http://localhost:8000/health`
- [ ] PostgreSQL receiving data: Check database logs
- [ ] PAPER_TRADING=true in .env file

---

## NEXT IMMEDIATE ACTIONS

1. **Create Workflows 2-5** following the step-by-step guide above
2. **Test each workflow** by clicking "Execute workflow"
3. **Verify Kite API** connection is working
4. **Run 30 days paper trading** with monitoring
5. **Verify all constraints** are enforced
6. **Go live** by changing PAPER_TRADING=false

---

## CRITICAL: Why Windsurf Doesn't Connect Directly to n8n

You asked about Windsurf and n8n connection. Here's why it's not needed:

- **Windsurf** = IDE for writing/editing code
- **n8n** = Workflow automation platform
- **Your Python microservices** = Run independently in Docker

**Flow**: Windsurf (edit code) → GitHub (commit) → Docker (run) → n8n (calls via HTTP)

n8n doesn't need to connect to Windsurf. Instead, n8n makes HTTP requests directly to your running Docker microservices on localhost:8000.

---

## PRODUCTION DEPLOYMENT

Once 30-day paper trading is verified:

1. Change in .env: `PAPER_TRADING=false`
2. Restart services: `docker-compose restart`
3. Verify live credentials loaded
4. Monitor P&L in PostgreSQL
5. Verify daily loss limit enforced at ₹20,000

---

**Status**: 1 of 5 workflows complete and active. Ready to create remaining 4.
