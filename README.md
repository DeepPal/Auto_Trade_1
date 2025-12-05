# 🎯 Professional Options Trading Setup
## Zerodha + n8n + Windsurf Integration

A complete, production-ready options trading system with multi-layer strategies, automated execution, and real-time monitoring.

## 📊 Architecture Overview

```
Windsurf (MCP) → n8n Workflows → Zerodha APIs
       ↓              ↓              ↓
   Control Panel   Automation    Execution
```

## 🚀 Quick Start

### Prerequisites
- Zerodha Trading Account + Kite Connect API subscription
- Docker & Docker Compose installed
- Python 3.9+ with pip
- Windsurf IDE with MCP support

### Installation

1. **Clone and Setup:**
```bash
# Clone repository
git clone <your-repo>
cd Trail_1

# Run automated setup
chmod +x setup.sh
./setup.sh
```

2. **Configure Credentials:**
```bash
# Copy and edit environment file
cp .env.template .env
nano .env  # Add your Zerodha API keys, tokens
```

3. **Start Services:**
```bash
docker-compose up -d
python test_connection.py  # Verify all connections
```

4. **Access Services:**
- n8n: http://localhost:5678 (admin/changeme)
- pgAdmin: http://localhost:5050 (admin@trading.local/admin)
- Grafana: http://localhost:3000 (admin/admin)

## 📁 Project Structure

```
Trail_1/
├── docker-compose.yml         # Container orchestration
├── requirements.txt           # Python dependencies
├── .env.template             # Environment template
├── setup.sh                  # Automated setup script
├── test_connection.py        # Connection validator
├── TRADING_SETUP_GUIDE.md   # Complete implementation guide
│
├── n8n_workflows/           # n8n workflow JSONs
│   ├── 01_kite_auth_workflow.json
│   └── 02_options_strategy_workflow.json
│
├── scripts/                 # Trading logic
│   ├── indicators.py       # Technical indicators
│   └── strategies/        # Strategy implementations
│
└── init_scripts/          # Database initialization
    └── 01_create_trading_schema.sql
```

## 🎯 Trading Strategies

### Implemented Strategies
1. **Iron Condor** - Delta neutral, high probability
2. **Short Strangle** - Premium collection in low volatility
3. **Calendar Spread** - Time decay arbitrage

### Multi-Layer Signal System
- **Layer 1:** Technical Indicators (40% weight)
  - RSI, MACD, EMA Crossover, Bollinger Bands, Supertrend
- **Layer 2:** Options Greeks (30% weight)
  - Delta targeting, Theta optimization, IV percentile
- **Layer 3:** Market Sentiment (20% weight)
  - VIX levels, Put-Call ratio, Volume profile
- **Layer 4:** Risk Management (10% weight)
  - Position sizing, Stop loss, Portfolio correlation

## 🔧 Configuration

### Strategy Parameters (.env)
```bash
MIN_SIGNAL_SCORE=70        # Minimum score to trigger trade
MAX_RISK_PER_TRADE=0.02    # 2% max risk per trade
MAX_DAILY_LOSS=0.03        # 3% daily loss limit
MAX_POSITIONS=5            # Maximum open positions
```

### n8n Workflow Import
1. Open n8n (http://localhost:5678)
2. Go to Workflows → Import
3. Import JSONs from `n8n_workflows/` folder
4. Activate workflows one by one

### Windsurf MCP Setup
Your `mcp_config.json` is already configured for n8n integration.

## 📈 Usage

### Manual Trading via Windsurf
```
@n8n-mcp place_order {"symbol":"NIFTY", "strategy":"iron_condor"}
@n8n-mcp get_positions
@n8n-mcp calculate_pnl
```

### Automated Trading
Workflows run automatically based on:
- Market open (9:15 AM IST) - Token refresh
- Every minute - Signal generation
- Signal threshold met - Order execution

## 🛡️ Risk Management

### Position Sizing
- Kelly Criterion based sizing
- Maximum 2% risk per trade
- Maximum 20% capital per position

### Stop Loss Rules
- Initial: 2% of capital or technical level
- Trailing: 50% of unrealized profit
- Daily limit: 3% max loss

### Safety Features
- Paper trading mode
- Manual approval for first week
- Automatic circuit breakers
- Real-time alerts (Telegram)

## 📊 Monitoring

### Performance Metrics
- View in Grafana dashboards
- Track win rate, Sharpe ratio, drawdown
- Real-time P&L monitoring

### Alerts
- Telegram notifications for signals
- Email alerts for errors
- Slack integration for team updates

## 🧪 Testing

### Backtesting
```python
python scripts/backtest.py --strategy iron_condor --period 2Y
```

### Paper Trading
Enable in `.env`:
```bash
PAPER_TRADING=true
```

## ⚠️ Important Notes

### Security
- **NEVER** commit `.env` file
- Rotate API tokens regularly
- Use strong passwords for all services
- Enable 2FA on Zerodha

### Compliance
- Follow SEBI regulations
- Maintain proper trade records
- Pay taxes on trading income
- Respect API rate limits

### Risk Disclaimer
Options trading involves substantial risk of loss. This system is for educational purposes. Always:
- Start with paper trading
- Test strategies thoroughly
- Never risk money you can't afford to lose
- Keep learning and adapting

## 📚 Documentation

- [Complete Setup Guide](TRADING_SETUP_GUIDE.md)
- [Kite Connect API](https://kite.trade/docs/connect/v3/)
- [n8n Documentation](https://docs.n8n.io/)
- [MCP Protocol](https://modelcontextprotocol.io/)

## 🤝 Support

For issues or questions:
1. Check `test_connection.py` for diagnostics
2. Review Docker logs: `docker-compose logs -f`
3. Consult TRADING_SETUP_GUIDE.md for detailed steps

## 📄 License

Personal use only. Not for commercial distribution.

---

**Remember:** Successful trading is 20% strategy, 30% risk management, and 50% psychology. Let the system handle execution while you focus on strategy improvement.
