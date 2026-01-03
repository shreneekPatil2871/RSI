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

# Note: Ensure you define send_email(content) here or import it

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

    all_results = []
    print(f"Scanning {len(nifty50)} stocks...")
    
    for ticker in nifty50:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            df['RSI'] = calculate_rsi_wilder(df['Close'], 14)
            last_rsi = float(df['RSI'].iloc[-1].item())
            last_price = float(df['Close'].iloc[-1].item())
            
            status = "Normal"
            if last_rsi < 30: status = "Oversold"
            elif last_rsi > 70: status = "Overbought"

            all_results.append({
                "Symbol": ticker, 
                "RSI": round(last_rsi, 2), 
                "Price": round(last_price, 2),
                "Status": status
            })
        except: continue
    
    # 1. Create DataFrames
    results_df = pd.DataFrame(all_results)
    
    # 2. FILTER: Only keep Overbought/Oversold for Website and Email
    filtered_df = results_df[results_df['Status'] != "Normal"].sort_values(by="RSI")
    
    # Build and Print Email Content
    report_text = f"NIFTY 50 RSI REPORT | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n" + "="*40 + "\n"
    if filtered_df.empty:
        report_text += "No stocks are currently in Overbought or Oversold zones."
    else:
        report_text += filtered_df.to_string(index=False)
    
    print(report_text)
    # send_email(report_text) # Uncomment this to enable email

    # 3. GENERATE HTML (Doubled braces {{ }} for CSS and JS to avoid f-string errors)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NIFTY 50 RSI Screener</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }}
            nav {{ margin-bottom: 30px; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            nav a {{ margin-right: 20px; text-decoration: none; color: #007bff; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background-color: #007bff; color: white; text-transform: uppercase; letter-spacing: 1px; }}
            .Oversold {{ color: #2ecc71; font-weight: bold; }}
            .Overbought {{ color: #e74c3c; font-weight: bold; }}
            .empty-msg {{ padding: 20px; text-align: center; color: #666; font-style: italic; }}
        </style>
    </head>
    <body>
        <h1>NIFTY 50 Market Screener</h1>
        
        <nav>
            <a href="#">🏠 Dashboard</a>
            <a href="#table-top">📊 RSI Zones</a>
            <a href="https://www.nseindia.com/" target="_blank">📈 NSE Live</a>
        </nav>

        <p><strong>Last Update:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} SGT</p>

        <div id="table-top">
            {filtered_df.to_html(index=False, classes='table', border=0) if not filtered_df.empty else '<div class="empty-msg">No stocks currently in Overbought or Oversold zones.</div>'}
        </div>

        <script>
            // Highlight the text colors
            document.querySelectorAll('td').forEach(td => {{
                if (td.innerText === 'Oversold') td.classList.add('Oversold');
                if (td.innerText === 'Overbought') td.classList.add('Overbought');
            }});
        </script>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Webpage (index.html) generated successfully!")

if __name__ == "__main__":
    run_nifty_screener()
