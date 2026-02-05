# PROJECT HOPE - Headless Options Trading Bot

A professional-grade headless options trading bot that runs 24/7 on Render with SMS alerts.

## Features

### 16 Protection Rules
1. ✅ -25% stop loss (hard stop)
2. ✅ +30% take profit (full exit)
3. ✅ +15% partial (sell 50%)
4. ✅ +25% partial (sell 25% more)
5. ✅ +10% move stop to breakeven
6. ✅ 4% daily loss limit (locks trading)
7. ✅ 10 min cooldown after any loss
8. ✅ Trading windows only (9:30-10:30 AM, 3:00-3:55 PM ET)
9. ✅ CHOP/MIXED regime blocks trades
10. ✅ 15 second signal confirmation
11. ✅ HOT score minimum 70
12. ✅ News blocking (bad news = no trade)
13. ✅ Earnings blackout (5 days before)
14. ✅ Option quality filters (spread, volume, OI)
15. ✅ Duplicate protection (no same stock twice)
16. ✅ Max 5 positions

### A+ Setups
- **Opening Range Break (ORB)** - Break above/below first 15 min range
- **VWAP Bounce** - Price bounces off VWAP in trend direction
- **Pullback Continuation** - EMA 9 pullback in trend
- **Break & Retest** - Key level broken and retested

### SMS Alerts For
- Trade entries with setup type and HOT score
- Take profits and stop losses
- Partial profits taken
- Breakeven stops set
- Market regime changes
- Daily loss limit warnings
- Cooldown periods
- Daily summaries

## Quick Start

### 1. Local Testing

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/PROJECT-HOPE-EDITION.git
cd PROJECT-HOPE-EDITION

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TRADIER_API_KEY="your_key"
export TRADIER_ACCOUNT_ID="your_account_id"
export TRADIER_BASE_URL="https://sandbox.tradier.com"
export TWILIO_ACCOUNT_SID="your_twilio_sid"
export TWILIO_AUTH_TOKEN="your_twilio_token"
export TWILIO_FROM_NUMBER="+1234567890"
export ALERT_PHONE_NUMBER="+1234567890"

# Run
python main.py
```

### 2. Deploy to Render

1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Background Worker**
4. Connect your GitHub repo
5. Configure:
   - **Name**: project-hope-bot
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
6. Add Environment Variables:
   - `TRADIER_API_KEY`
   - `TRADIER_ACCOUNT_ID`
   - `TRADIER_BASE_URL`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER`
   - `ALERT_PHONE_NUMBER`
7. Click **Deploy**

### 3. Monitor

- **Render Logs**: Check live logs in Render dashboard
- **SMS Alerts**: You'll get texts for all trading activity
- **Tradier Dashboard**: View positions at tradier.com

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRADIER_API_KEY` | ✅ | Your Tradier API key |
| `TRADIER_ACCOUNT_ID` | ✅ | Your Tradier account ID |
| `TRADIER_BASE_URL` | ❌ | `https://sandbox.tradier.com` (default) or `https://api.tradier.com` |
| `TWILIO_ACCOUNT_SID` | ❌ | Twilio SID for SMS alerts |
| `TWILIO_AUTH_TOKEN` | ❌ | Twilio auth token |
| `TWILIO_FROM_NUMBER` | ❌ | Your Twilio phone number |
| `ALERT_PHONE_NUMBER` | ❌ | Your phone to receive alerts |

## File Structure

```
project-hope-headless/
├── main.py              # Entry point
├── config.py            # Configuration & settings
├── trading_engine.py    # Main trading loop
├── market_analyzer.py   # Technical analysis & signals
├── position_manager.py  # Position tracking & management
├── tradier_client.py    # Tradier API wrapper
├── alert_service.py     # Twilio SMS alerts
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
└── README.md            # This file
```

## Trading Logic

### Market Regime (SPY-based)
- **TREND** (0-2 VWAP crosses): ✅ Trading enabled
- **MIXED** (3 crosses): ❌ No new trades
- **CHOP** (4+ crosses): ❌ No new trades

### HOT Score Calculation (0-100)
- RVOL (relative volume): up to 30 pts
- Near key level: 20 pts
- TREND regime: 20 pts
- Volume spike (2x+): 15 pts
- Tight spread: 10 pts
- Positive news: 5 pts
- **Minimum 70 to trade**

### Position Sizing
- 5% of account per trade
- Max 5 positions open

### Trading Windows (ET)
- Morning: 9:30 AM - 10:30 AM
- Power Hour: 3:00 PM - 3:55 PM

## Going Live

1. Change `TRADIER_BASE_URL` to `https://api.tradier.com`
2. Fund your Tradier account
3. Start small, monitor closely
4. Scale up once confident

## Support

Built for PROJECT HOPE. Your family's future depends on disciplined execution.

Stay disciplined. Trust the system. 🎯
