import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime
import io

def send_line_message(messages_list):
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
    
    # ส่งข้อความแบบ Array (ส่งได้สูงสุด 5 บอลลูนพร้อมกัน)
    payload = {
        "to": user_id,
        "messages": messages_list[:5]
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

    # ดึงข้อมูลทั้งหมด
    print(f"Downloading data for all {len(tickers)} tickers...")
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    results = []
    
    for ticker in tickers:
        try:
            if ticker not in data: continue
            df = data[ticker].copy()
                
            df = df.dropna()
            if len(df) < 200: continue
            
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            
            last = df.iloc[-1]
            
            # ใช้เกณฑ์ Uptrend พื้นฐานตามที่คุณต้องการ
            cond_uptrend = last['Close'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200']
            
            if cond_uptrend:
                results.append(f"🟢 {ticker} | Price: ${last['Close']:.2f}")
                
        except Exception as e:
            continue
            
    # สรุปผลและแบ่งข้อความเพื่อหลบข้อจำกัด 5,000 ตัวอักษรของ LINE
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if results:
        messages = []
        chunk_size = 50  # แบ่งหุ้นออกเป็นกลุ่มละ 50 ตัวต่อ 1 บอลลูนแชท
        
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i+chunk_size]
            text = "\n".join(chunk)
            
            # ใส่ส่วนหัวเฉพาะข้อความกล่องแรก
            if i == 0:
                text = f"📊 S&P 500 Uptrend Screener ({date_str})\n(พบหุ้นขาขึ้น {len(results)} ตัว)\n\n" + text
                
            messages.append({"type": "text", "text": text})
            
        send_line_message(messages)
    else:
        msg = f"📉 S&P 500 Screener ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Uptrend ในวันนี้"
        send_line_message([{"type": "text", "text": msg}])
        
    print("Done!")

if __name__ == "__main__":
    main()
