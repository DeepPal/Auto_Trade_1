# N8N Workflow Import Setup Guide

## Overview

You have production-ready n8n workflows in your local repository (in `n8n_workflows/` folder). This guide walks you through importing them into n8n.

## Prerequisites

✅ Docker containers running: `docker-compose up -d`
✅ n8n accessible at: http://localhost:5678
✅ Repository synced locally: `C:/Users/deepp/Desktop/Trail_1/`
✅ PostgreSQL running on localhost:5432

## Step 1: Start Fresh (Optional)

If you want a clean start, delete the current "My workflow 2" in n8n:
1. Go to http://localhost:5678/home/workflows
2. Right-click "My workflow 2"
3. Select Delete

## Step 2: Import Workflows (In Order)

### Import Workflow 00: Test Workflow

**File**: `n8n_workflows/00_TEST_WORKFLOW.json`

**Steps**:
1. Go to http://localhost:5678
2. Click "+ New" (or create new workflow)
3. Click the **three-dot menu** (top right) → **Import from File...**
4. Select: `C:/Users/deepp/Desktop/Trail_1/n8n_workflows/00_TEST_WORKFLOW.json`
5. n8n will import the workflow
6. **Save** the workflow
7. Copy the **Workflow ID** from the URL bar (format: `workflow/ABC123XYZ/...`)

**Purpose**: Sanity check - test webhook triggers and HTTP connections
**Trigger**: Webhook at `/webhook/test-signal`

---

### Import Workflow 01: Kite Auth

**File**: `n8n_workflows/01_kite_auth_workflow.json`

**Steps**:
1. Create a new workflow
2. Import from File: `01_kite_auth_workflow.json`
3. Save it
4. Copy the **Workflow ID**

**Purpose**: Token refresh from Zerodha Kite
**Trigger**: Schedule (9:15 AM daily)
**Action**: POST to `/token` endpoint

---

### Import Workflow 03: Iron Condor Strategy

**File**: `n8n_workflows/03_iron_condor_strategy.json`

**Steps**:
1. Create a new workflow
2. Import from File: `03_iron_condor_strategy.json`
3. Save it
4. Copy the **Workflow ID**

**Purpose**: Iron Condor strategy signal generation and order execution
**Trigger**: Scheduled (configurable frequency)
**Action**: Generates signals, checks conditions, executes orders

---

### Import Workflow: MASTER Trading Orchestrator

**File**: `n8n_workflows/MASTER_TRADING_ORCHESTRATOR.json`

**Steps**:
1. Create a new workflow
2. Import from File: `MASTER_TRADING_ORCHESTRATOR.json`
3. Save it

**Purpose**: Central scheduler that triggers all other workflows
**Trigger**: Schedule (market open hours)
**Action**: Calls execute-workflow nodes for each strategy

---

## Step 3: Configure Workflow IDs in Master Orchestrator

The Master Orchestrator uses "Execute Workflow" nodes to call other workflows. You need to wire the actual Workflow IDs.

### Find Workflow IDs:

For each imported workflow, open it and copy the ID from the URL:
- URL: `http://localhost:5678/workflow/YOUR_WORKFLOW_ID_HERE/...`
- Example: If URL is `http://localhost:5678/workflow/abc123xyz456/editor`, then ID = `abc123xyz456`

### Update Master Orchestrator:

1. Open **MASTER_TRADING_ORCHESTRATOR** workflow
2. Click on each "Execute Workflow" node
3. In the node properties, paste the corresponding Workflow ID:
   - **Execute Kite Auth** → Paste `01_kite_auth_workflow` ID
   - **Execute Signal Generation** → Paste `03_iron_condor_strategy` ID
   - **Execute Order Executor** → Paste order executor workflow ID (if separate)
4. **Save** the workflow

## Step 4: Set Up Credentials

All workflows need credentials to connect to external services.

### HTTP Header Auth (for Kite API)

1. Go to Credentials tab
2. Create new credential: "HTTP Header Auth"
3. Name: `Kite_API_Auth`
4. Headers:
   ```
   Authorization: token YOUR_KITE_ACCESS_TOKEN
   ```
5. Save

### PostgreSQL Credential

1. Create new credential: "PostgreSQL"
2. Name: `Trading_DB`
3. Settings:
   - **Host**: `localhost`
   - **Port**: `5432`
   - **Database**: (from your .env)
   - **User**: (from your .env)
   - **Password**: (from your .env)
4. Save

### Telegram (Optional)

1. Create new credential: "Telegram"
2. Name: `Telegram_Bot`
3. Settings:
   - **Access Token**: (your bot token)
   - **Chat ID**: (your chat ID)
4. Save

## Step 5: Configure .env Secrets

The workflows need actual secrets to function. **Edit your `.env` file** (NOT committed):

```bash
# Zerodha Kite
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token
KITE_USER_ID=your_user_id
KITE_PASSWORD=your_password

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trader
DB_PASSWORD=your_password

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Paper Trading Mode
PAPER_TRADING=true  # Keep true until you've tested thoroughly

# Trading Parameters
DAILY_LOSS_LIMIT=20000  # Rs 20,000
MAX_TRADES_PER_DAY=3
MAX_OPEN_POSITIONS=4
```

**After editing .env:**
```bash
docker-compose restart
```

## Step 6: Test the Workflows

### Test 00_TEST_WORKFLOW

**Via curl:**
```bash
curl -X POST http://localhost:5678/webhook/test-signal \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "strategy": "IRON_CONDOR",
    "action": "test"
  }'
```

**In n8n UI:**
1. Open `00_TEST_WORKFLOW`
2. Click "Execute workflow" button
3. Check "Executions" tab for results

### Test 01_kite_auth_workflow

**In n8n UI:**
1. Open `01_kite_auth_workflow`
2. Click "Execute workflow"
3. Should show successful token refresh
4. Check PostgreSQL logs table

### Test 03_iron_condor_strategy

**In n8n UI:**
1. Open `03_iron_condor_strategy`
2. Click "Execute workflow"
3. Should generate signals and log to database
4. Check PostgreSQL `signals` table for entries

## Step 7: Activate Master Orchestrator

Once all workflows are imported, tested, and IDs are wired:

1. Open **MASTER_TRADING_ORCHESTRATOR**
2. Toggle "Inactive" to "Active"
3. Verify it runs on schedule
4. Check Executions tab for logs

## Step 8: Verify Paper Trading Mode

**CRITICAL**: Ensure paper trading is enabled before live trading:

1. Check `.env`: `PAPER_TRADING=true`
2. Restart containers: `docker-compose restart`
3. Check order executor logs: `docker logs order_executor`
4. Verify orders execute in paper mode (no real positions opened)

## Troubleshooting

### Issue: "Workflow ID not found"
- **Cause**: Placeholder ID in Execute Workflow nodes
- **Fix**: Replace with actual IDs from imported workflows

### Issue: "Connection refused on localhost:8000"
- **Cause**: Microservices not running
- **Fix**: `docker-compose up -d` and verify with `curl http://localhost:8000/health`

### Issue: "PostgreSQL credential error"
- **Cause**: Wrong host/port/password
- **Fix**: Check `.env` and verify Docker network: `docker network ls`

### Issue: "Webhook not triggering"
- **Cause**: Webhook URL mismatch
- **Fix**: Copy exact URL from workflow webhook node

### Issue: "n8n container doesn't see updated .env"
- **Cause**: Container needs restart after .env changes
- **Fix**: `docker-compose restart n8n`

## Activation Checklist

- [ ] All 4 workflows imported (00, 01, 03, MASTER)
- [ ] Workflow IDs extracted and verified
- [ ] Workflow IDs wired in Master Orchestrator
- [ ] Credentials created (HTTP Auth, PostgreSQL, Telegram)
- [ ] .env file populated with secrets
- [ ] Containers restarted after .env changes
- [ ] Test workflow executes successfully
- [ ] Kite auth workflow refreshes token
- [ ] Iron Condor workflow generates signals
- [ ] Master Orchestrator activates without errors
- [ ] Paper trading mode verified (PAPER_TRADING=true)
- [ ] All 3 risk constraints enforced:
  - Daily loss limit: ₹20,000
  - Max trades/day: 3
  - Max open positions: 4

## Next Steps

1. ✅ Import all workflows
2. ✅ Wire Workflow IDs
3. ✅ Configure credentials
4. ✅ Populate .env secrets
5. ✅ Test each workflow
6. ✅ Enable Master Orchestrator
7. ⏳ Run 30-day paper trading validation
8. ⏳ Verify risk constraints working
9. ⏳ Go live (change PAPER_TRADING=false)

## Contact & Support

If you encounter issues:
1. Check n8n execution logs: Executions tab
2. Check Docker logs: `docker logs n8n`
3. Test microservices: `curl http://localhost:8000/health`
4. Verify PostgreSQL: `docker exec postgres psql -U trader -d trading_db -c "SELECT 1"`

---

**Status**: Ready for import. All 4 workflows can be imported immediately from the `n8n_workflows/` folder.
