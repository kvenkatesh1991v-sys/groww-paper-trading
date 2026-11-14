# Groww F&O Paper Trading Bot — Android-friendly prototype

This is a browser-based Streamlit paper-trading ledger. It does **not** connect to Groww,
does **not** fetch live NSE prices, and never places real orders. Enter option premiums
manually from the Groww app.

## Run on a computer

1. Install Python 3.10 or newer.
2. Extract this ZIP and open a terminal in the extracted folder.
3. Run:

   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py

4. Open the URL shown by Streamlit.

## Use on Android

For phone-only use, deploy this folder to a private GitHub repository and deploy it
with Streamlit Community Cloud. Open the deployed app URL in Chrome and use
"Add to Home screen". The app stores its SQLite database in its running environment;
some hosted environments may reset local files on restart/redeploy. For persistent
hosted storage, add a managed database before relying on long-term records.

## Current features

- ₹10,000 virtual starting equity
- NIFTY and BANKNIFTY CE/PE paper BUY entries
- Manual entry/current premium, stop loss and target
- Virtual open P&L and closed P&L
- Per-trade risk cap ₹50, daily loss cap ₹100, max 2 entries/day
- CSV trade-history export

## Important limitations

- No Groww API integration or live price feed
- No automatic entry/exit or stop-loss triggering
- Quantity is entered as option units; this prototype does not validate current exchange lot sizes
- Brokerage, STT, GST, exchange charges, slippage, spreads and option Greeks are not included
- Risk controls are prototype guardrails, not a guarantee against loss

Do not add Groww API keys to this code or commit secrets to GitHub. A later integration
should use Groww's official API documentation, secure server-side secrets, current
exchange lot-size data, and a separate paper execution engine.
