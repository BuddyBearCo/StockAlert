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
    # อัปเดต: เพิ่ม User-Agent เพื่อป้องกัน Wikipedia บล็อกการดึงข้อมูล
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    html_data = requests.get(url, headers=headers).text
    
    table = pd.read_html(io.StringIO(html_data))
    tickers = table[0]['Symbol'].str.replace('.', '-').tolist()
    
    # จำกัดจำนวนหุ้นเพื่อทดสอบความรวดเร็ว
    tickers = tickers[:100] 
    
    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    results = []
    
    for ticker in tickers:
        try:
            df = data[ticker].copy()
            df = df.dropna()
            if len(df) < 200: continue
            
            # คำนวณ Indicators
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.sma(close="Volume", length=50, append=True)
            df.ta.adx(length=14, append=True)
            
            last = df.iloc[-1]
            prev20 = df.iloc[-21]
            
            # เช็คเงื่อนไข Strict Mode
            cond1 = last['Close'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200']
            cond2 = last['EMA_200'] > prev20['EMA_200'] 
            cond3 = last['Close'] > last['Open'] 
            cond4 = last['Volume'] > (last['SMA_50'] * 1.5) 
            cond5 = last['ADX_14'] > 25 and last['DMP_14'] > last['DMN_14'] 
            
            if cond1 and cond2 and cond3 and cond4 and cond5:
                results.append(f"🟢 {ticker} | Price: ${last['Close']:.2f}")
                
        except Exception as e:
            continue
            
    # สรุปผลและส่งเข้า LINE
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if results:
        msg = f"🔥 S&P 500 Trend Screener ({date_str})\n\n" + "\n".join(results)
    else:
        msg = f"📉 S&P 500 Trend Screener ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Strict Mode ในวันนี้"
        
    send_line_message(msg)
    print("Done!")

if __name__ == "__main__":
    main()    # จำกัดจำนวนหุ้นเพื่อความรวดเร็วในการสแกน
    tickers = tickers[:100] 
    
    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    results = []
    
    for ticker in tickers:
        try:
            df = data[ticker].copy()
            df = df.dropna()
            if len(df) < 200: continue
            
            # คำนวณ Indicators
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.sma(close="Volume", length=50, append=True)
            df.ta.adx(length=14, append=True)
            
            last = df.iloc[-1]
            prev20 = df.iloc[-21]
            
            # เช็คเงื่อนไข Strict Mode
            cond1 = last['Close'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200']
            cond2 = last['EMA_200'] > prev20['EMA_200'] 
            cond3 = last['Close'] > last['Open'] 
            cond4 = last['Volume'] > (last['SMA_50'] * 1.5) 
            cond5 = last['ADX_14'] > 25 and last['DMP_14'] > last['DMN_14'] 
            
            if cond1 and cond2 and cond3 and cond4 and cond5:
                results.append(f"🟢 {ticker} | Price: ${last['Close']:.2f}")
                
        except Exception as e:
            continue
            
    # สรุปผลและส่งเข้า LINE
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    if results:
        msg = f"🔥 S&P 500 Trend Screener ({date_str})\n\n" + "\n".join(results)
    else:
        msg = f"📉 S&P 500 Trend Screener ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Strict Mode ในวันนี้"
        
    send_line_message(msg)
    print("Done!")

if __name__ == "__main__":
    main()
