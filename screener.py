import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime
import io

def send_line_message(message):
    # ดึงมาแค่ Token อย่างเดียว ไม่ต้องใช้ USER_ID แล้ว
    token = os.environ.get("LINE_TOKEN")
    
    if not token:
        print("Missing LINE credentials")
        return
        
    # เปลี่ยน URL ปลายทางเป็นคำว่า broadcast
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Payload รอบนี้ไม่ต้องมีคำว่า "to" เพราะระบบจะส่งหาเพื่อนทุกคนให้อัตโนมัติ
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("LINE broadcast sent successfully to all followers.")
    else:
        print(f"Error sending broadcast: {response.status_code} - {response.text}")

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
        print(f"Warning: Could not fetch from Wikipedia.")
        tickers = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK-B', 'LLY', 'AVGO', 'JPM']

    print(f"Downloading data for {len(tickers)} tickers...")
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    passed_stocks = []
    
    for ticker in tickers:
        try:
            if ticker not in data: continue
            df = data[ticker].copy()
            df = df.dropna()
            if len(df) < 200: continue
            
            df.ta.ema(length=20, append=True)
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.adx(length=14, append=True)
            
            last = df.iloc[-1]
            
            # เกณฑ์ Perfect Uptrend + ADX > 25
            cond_trend = (last['Close'] > last['EMA_20']) and (last['EMA_20'] > last['EMA_50']) and (last['EMA_50'] > last['EMA_200'])
            cond_adx = last['ADX_14'] > 25 and last['DMP_14'] > last['DMN_14']
            
            if cond_trend and cond_adx:
                passed_stocks.append({
                    'ticker': ticker,
                    'price': last['Close'],
                    'adx': last['ADX_14']
                })
                
        except Exception as e:
            continue
            
    top_stocks = sorted(passed_stocks, key=lambda x: x['adx'], reverse=True)[:15]
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if top_stocks:
        results_text = [f"🟢 {s['ticker']} | P: ${s['price']:.2f} | ADX: {s['adx']:.1f}" for s in top_stocks]
        msg = f"🇺🇸 American Top 15 Strongest Trend\n({date_str})\n\n" + "\n".join(results_text)
        
        if len(passed_stocks) > 15:
            msg += f"\n\n*(คัดจากหุ้นขาขึ้นทั้งหมด {len(passed_stocks)} ตัว)*"
            
        send_line_message(msg)
    else:
        msg = f"📉 S&P 500 Screener ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Strong Trend ในวันนี้"
        send_line_message(msg)
        
    print("Done!")

if __name__ == "__main__":
    main()
