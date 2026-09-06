import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime
import io

def send_line_message(message):
    token = os.environ.get("LINE_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    
    if not token or not user_id:
        print("Missing LINE credentials")
        return
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("LINE message sent successfully.")
    else:
        print(f"Error sending to LINE: {response.status_code} - {response.text}")

def main():
    print("Fetching S&P 500 tickers...")
    tickers = []
    
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_data = requests.get(url, headers=headers).text
        table = pd.read_html(io.StringIO(html_data))
        tickers = table[0]['Symbol'].str.replace('.', '-').tolist()
    except Exception as e:
        print(f"Warning: Could not fetch from Wikipedia ({e}), using backup list.")
        tickers = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK-B', 'LLY', 'AVGO', 'JPM', 'XOM', 'TSLA', 'UNH', 'V', 'PG', 'MA', 'HD', 'COST', 'JNJ', 'NFLX']

    # ปรับสแกนเพิ่มจำนวนหุ้นให้ครอบคลุมมากขึ้น (เช่น 200 ตัวแรก)
    tickers = tickers[:200] 
    
    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    results = []
    
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                df = data.copy()
            else:
                if ticker not in data: continue
                df = data[ticker].copy()
                
            df = df.dropna()
            if len(df) < 200: continue
            
            # คำนวณ Indicators
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            
            last = df.iloc[-1]
            
            # ปรับเกณฑ์เหลือเฉพาะข้อที่ 1: ราคาปิด > EMA50 และ EMA50 > EMA200 (Uptrend พื้นฐาน)
            cond_uptrend = last['Close'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200']
            
            if cond_uptrend:
                results.append(f"🟢 {ticker} | Price: ${last['Close']:.2f}")
                
        except Exception as e:
            continue
            
    # สรุปผลและส่งเข้า LINE
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if results:
        # จำกัดการแสดงผลไม่ให้ข้อความยาวเกินไปใน LINE (แสดงสัก 25 ตัวแรกที่เจอ)
        display_results = results[:25]
        msg = f"📊 S&P 500 Uptrend Screener ({date_str})\n(พบหุ้นขาขึ้น {len(results)} ตัว)\n\n" + "\n".join(display_results)
        if len(results) > 25:
            msg += f"\n\n...และอื่นๆอีก {len(results) - 25} ตัว"
    else:
        msg = f"📉 S&P 500 Screener ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Uptrend ในวันนี้"
        
    send_line_message(msg)
    print("Done!")

if __name__ == "__main__":
    main()
