import yfinance as yf
import pandas as pd
import warnings
import smtplib
import os
from email.mime.text import MIMEText

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def calculate_rsi_wilder(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def send_email(content):
    sender_email = ""
    receiver_email = ""
    password = os.getenv("") 

    if not password:
        print("Error: EMAIL_PASSWORD environment variable not set.")
        return

    msg = MIMEText(content)
    msg['Subject'] = f"NIFTY 50 RSI Report: {pd.Timestamp.now().strftime('%d %b %Y')}"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def run_nifty_screener():
    nifty50 = [
        "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
        "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BPCL.NS",
        "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
        "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
        "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ITC.NS",
        "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
        "LTIM.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS",
        "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SUNPHARMA.NS",
        "TCS.NS", "TATACONSUM.NS",  "TATASTEEL.NS", "TECHM.NS",
        "TITAN.NS", "ULTRACEMCO.NS", "TRENT.NS", "WIPRO.NS"
    ]

    oversold, overbought = [], []
    print(f"Scanning {len(nifty50)} stocks...")
    
    for ticker in nifty50:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            df['RSI'] = calculate_rsi_wilder(df['Close'], 14)
            last_rsi = float(df['RSI'].iloc[-1].item())
            last_price = float(df['Close'].iloc[-1].item())
            
            stock_info = {"symbol": ticker, "rsi": round(last_rsi, 2), "price": round(last_price, 2)}
            if last_rsi < 30: oversold.append(stock_info)
            elif last_rsi > 70: overbought.append(stock_info)
        except: continue

    # Build Report String
    report = [f"NIFTY 50 RSI REPORT | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n" + "="*40]
    
    report.append(f"\n📉 OVERSOLD (RSI < 30): {len(oversold)}")
    for s in sorted(oversold, key=lambda x: x['rsi']):
        report.append(f"{s['symbol']:<15} | RSI: {s['rsi']:>6} | Price: ₹{s['price']:,.2f}")
    
    report.append(f"\n📈 OVERBOUGHT (RSI > 70): {len(overbought)}")
    for s in sorted(overbought, key=lambda x: x['rsi'], reverse=True):
        report.append(f"{s['symbol']:<15} | RSI: {s['rsi']:>6} | Price: ₹{s['price']:,.2f}")

    final_report = "\n".join(report)
    print(final_report)
    send_email(final_report)

if __name__ == "__main__":

    run_nifty_screener()
