import sqlite3
from datetime import datetime, date
import streamlit as st
import pandas as pd

DB = "paper_trading.db"
STARTING_CAPITAL = 10000.0
RISK_PER_TRADE = 50.0
DAILY_LOSS_LIMIT = 100.0
MAX_TRADES_PER_DAY = 2

st.set_page_config(page_title="F&O Paper Trading", page_icon="📈", layout="centered")

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                index_name TEXT NOT NULL,
                option_type TEXT NOT NULL,
                strike TEXT NOT NULL,
                expiry TEXT NOT NULL,
                entry_premium REAL NOT NULL,
                current_premium REAL NOT NULL,
                stop_loss REAL NOT NULL,
                target REAL NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                realized_pnl REAL DEFAULT 0
            )
        """)

def read_trades():
    with db() as con:
        return pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC", con)

def open_trades():
    df = read_trades()
    return df[df["status"] == "OPEN"].copy() if not df.empty else df
    
def totals():
    df = read_trades()
    if df.empty:
        return 0.0, 0.0, 0, 0.0
    realized = float(df.loc[df.status == "CLOSED", "realized_pnl"].sum())
    op = df[df.status == "OPEN"]
    unrealized = float(((op.current_premium - op.entry_premium) * op.quantity).sum()) if not op.empty else 0.0
    today = date.today().isoformat()
    today_closed = df[(df.status == "CLOSED") & (df.closed_at.str[:10] == today)]
    today_open = df[(df.status == "OPEN") & (df.opened_at.str[:10] == today)]
    today_pnl = float(today_closed.realized_pnl.sum())
    if not today_open.empty:
        today_pnl += float(((today_open.current_premium - today_open.entry_premium) * today_open.quantity).sum())
    today_count = int((df.opened_at.str[:10] == today).sum())
    return realized, unrealized, today_count, today_pnl

def money(x):
    return f"₹{x:,.2f}"

init_db()
st.title("📈 Groww F&O Paper Trading")
st.caption("Mobile-friendly practice ledger • ₹10,000 virtual capital • No real orders")

st.warning(
    "Prototype mode: this app does NOT connect to Groww and does NOT fetch live NSE prices. "
    "Enter the option premium shown in your Groww app manually. All trades here are virtual."
)

realized, unrealized, today_count, today_pnl = totals()
equity = STARTING_CAPITAL + realized + unrealized
m1, m2 = st.columns(2)
m1.metric("Virtual equity", money(equity))
m2.metric("Today's P&L", money(today_pnl), delta=money(today_pnl))
m3, m4 = st.columns(2)
m3.metric("Realized P&L", money(realized))
m4.metric("Open P&L", money(unrealized))

tab_trade, tab_positions, tab_history, tab_rules = st.tabs(
    ["New trade", "Open positions", "History", "Rules"]
)

with tab_trade:
    st.subheader("Create a virtual options trade")
    st.caption("Use the exact option premium from Groww. Quantity means number of option units, not lots.")
    with st.form("new_trade"):
        index_name = st.selectbox("Index", ["NIFTY", "BANKNIFTY"])
        option_type = st.radio("Option type", ["CE", "PE"], horizontal=True)
        strike = st.text_input("Strike price", placeholder="Example: 24500")
        expiry = st.text_input("Expiry date", placeholder="YYYY-MM-DD")
        entry = st.number_input("Entry premium (₹)", min_value=0.05, value=100.0, step=0.05)
        sl = st.number_input("Stop-loss premium (₹)", min_value=0.05, value=80.0, step=0.05)
        target = st.number_input("Target premium (₹)", min_value=0.05, value=130.0, step=0.05)
        qty = st.number_input("Quantity (units)", min_value=1, max_value=10000, value=1, step=1)
        risk = max(0.0, (entry - sl) * qty)
        st.info(f"Estimated risk to stop-loss: {money(risk)}")
        submit = st.form_submit_button("Save paper BUY", use_container_width=True)

    if submit:
        errors = []
        if not strike.strip():
            errors.append("Enter the option strike.")
        try:
            datetime.strptime(expiry.strip(), "%Y-%m-%d")
        except Exception:
            errors.append("Expiry must be YYYY-MM-DD.")
        if not (sl < entry < target):
            errors.append("For a long option trade, Stop-loss must be below entry and target above entry.")
        if risk > RISK_PER_TRADE:
            errors.append(f"Risk exceeds the prototype limit of {money(RISK_PER_TRADE)} per trade.")
        if today_count >= MAX_TRADES_PER_DAY:
            errors.append(f"Daily trade limit reached ({MAX_TRADES_PER_DAY}).")
        if today_pnl <= -DAILY_LOSS_LIMIT:
            errors.append("Daily loss limit reached. No new trades allowed.")
        if entry * qty > equity:
            errors.append("Premium cost is higher than available virtual equity.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            now = datetime.now().isoformat(timespec="seconds")
            with db() as con:
                con.execute("""
                    INSERT INTO trades
                    (opened_at,index_name,option_type,strike,expiry,entry_premium,current_premium,
                     stop_loss,target,quantity,status,realized_pnl)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,0)
                """, (now,index_name,option_type,strike.strip(),expiry.strip(),entry,entry,sl,target,int(qty),"OPEN"))
            st.success("Paper trade saved. No real order was placed.")
            st.rerun()

with tab_positions:
    st.subheader("Open positions")
    op = open_trades()
    if op.empty:
        st.info("No open paper positions.")
    else:
        for _, r in op.iterrows():
            with st.container(border=True):
                st.markdown(f"**#{int(r.id)} {r.index_name} {r.strike} {r.option_type}**")
                st.caption(f"Expiry: {r.expiry} • Qty: {int(r.quantity)} • Opened: {r.opened_at}")
                a, b = st.columns(2)
                a.write(f"Entry: **{money(r.entry_premium)}**")
                b.write(f"Current: **{money(r.current_premium)}**")
                pnl = (r.current_premium-r.entry_premium)*r.quantity
                st.metric("Unrealized P&L", money(pnl))
                with st.form(f"update_{int(r.id)}"):
                    new_premium = st.number_input(
                        "Update current option premium (₹)", min_value=0.05,
                        value=float(r.current_premium), step=0.05, key=f"prem_{int(r.id)}"
                    )
                    c1, c2 = st.columns(2)
                    update = c1.form_submit_button("Update price", use_container_width=True)
                    close = c2.form_submit_button("Close position", use_container_width=True)
                if update:
                    with db() as con:
                        con.execute("UPDATE trades SET current_premium=? WHERE id=?", (new_premium,int(r.id)))
                    st.rerun()
                if close:
                    final_pnl = (new_premium-r.entry_premium)*r.quantity
                    with db() as con:
                        con.execute("""
                            UPDATE trades SET current_premium=?, status='CLOSED',
                            closed_at=?, realized_pnl=? WHERE id=?
                        """, (new_premium,datetime.now().isoformat(timespec="seconds"),final_pnl,int(r.id)))
                    st.success(f"Position closed. Realized P&L: {money(final_pnl)}")
                    st.rerun()

with tab_history:
    st.subheader("Trade history")
    hist = read_trades()
    if hist.empty:
        st.info("No trades recorded yet.")
    else:
        view = hist[["id","opened_at","index_name","strike","option_type","entry_premium",
                     "current_premium","quantity","status","realized_pnl"]].copy()
        view.columns = ["ID","Opened","Index","Strike","Type","Entry ₹","Latest/Exit ₹","Qty","Status","Realized P&L ₹"]
        st.dataframe(view, use_container_width=True, hide_index=True)
        csv = hist.to_csv(index=False).encode("utf-8")
        st.download_button("Download trade history CSV", csv, "paper_trade_history.csv", "text/csv")

with tab_rules:
    st.subheader("Prototype risk rules")
    st.markdown(f"""
    - Starting virtual capital: **{money(STARTING_CAPITAL)}**
    - Maximum planned loss per trade: **{money(RISK_PER_TRADE)}**
    - Daily loss stop: **{money(DAILY_LOSS_LIMIT)}**
    - Maximum entries per day: **{MAX_TRADES_PER_DAY}**
    - Only long option BUY trades (CE/PE) are supported.
    - No averaging, no real orders, no automatic execution.
    """)
    st.caption(
        "These are conservative prototype limits, not a recommendation or a guarantee. "
        "The app does not yet calculate brokerage, taxes, slippage, lot-size rules or option Greeks."
    )

st.divider()
st.caption("For learning only. Verify expiry, strike, lot size and premium independently. F&O can cause rapid losses.")
