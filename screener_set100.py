import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime
import pytz

def send_line_message(message):
    token = os.environ.get("LINE_TOKEN")
    if not token:
        print("Missing LINE credentials")
        return
        
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("LINE broadcast sent successfully.")
    else:
        print(f"Error sending broadcast: {response.status_code} - {response.text}")

def main():
    print("Loading tickers from tickers.txt")
    
    # 1. คำสั่งให้อ่านรายชื่อหุ้นจากไฟล์ tickers.txt
    try:
        with open("tickers.txt", "r") as file:
            # อ่านทีละบรรทัด ลบช่องว่างทิ้ง และข้ามบรรทัดที่ว่างเปล่า
            symbols = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: ไม่พบไฟล์ tickers.txt บน GitHub")
        return

    # 2. เติม .BK ต่อท้ายชื่อหุ้นทุกตัว เพื่อให้ระบบ yfinance ดึงข้อมูลหุ้นไทยได้
    tickers = [f"{sym}.BK" for sym in symbols]

    print(f"Total tickers loaded: {len(tickers)} symbols")
    print(f"Downloading data...")
    
    # ดึงข้อมูลหุ้นทั้งหมดพร้อมกัน
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
            
            last = df.iloc[-1]
            close_price = last['Close']
            ema20 = last['EMA_20']
            ema50 = last['EMA_50']
            ema200 = last['EMA_200']
            
            # เงื่อนไขเทรนด์ขาขึ้น
            cond_trend = (close_price > ema20) and (ema20 > ema50) and (ema50 > ema200)
            
            if cond_trend:
                # คำนวณแรงผลัก (% ห่างจาก EMA200)
                pct_above_ema200 = ((close_price - ema200) / ema200) * 100
                
                # กรองเฉพาะหุ้นที่มีแรงผลักอยู่ในช่วง 3% ถึง 12%
                if 3.0 <= pct_above_ema200 <= 12.0:
                    display_name = ticker.replace(".BK", "")
                    passed_stocks.append({
                        'ticker': display_name,
                        'price': close_price,
                        'power': pct_above_ema200
                    })
                
        except Exception as e:
            continue
            
    # เรียงลำดับหุ้นที่เข้าเกณฑ์ โดยให้ตัวที่มีแรงผลักมากที่สุดอยู่ด้านบน (แสดงผลสูงสุด 15 ตัว)
    top_stocks = sorted(passed_stocks, key=lambda x: x['power'], reverse=True)[:15]
    
    # ตั้งค่าเวลาให้ตรงกับประเทศไทย
    tz = pytz.timezone('Asia/Bangkok')
    time_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    # 3. จัดรูปแบบข้อความเพื่อส่งเข้า LINE
    if top_stocks:
        results_text = [f"🟢 {s['ticker']} | ฿{s['price']:.2f} | แรงผลัก: +{s['power']:.1f}%" for s in top_stocks]
        msg = f"🇹🇭 หุ้น SET/MAI แรงผลัก 3-12%\n({time_str})\n\n" + "\n".join(results_text)
        send_line_message(msg)
    else:
        msg = f"📉 สแกนหุ้นไทย (SET/MAI)\n({time_str})\n\nไม่มีหุ้นเข้าเกณฑ์แรงผลัก 3-12% ในรอบนี้"
        send_line_message(msg)
        
    print("Done!")

if __name__ == "__main__":
    main()
