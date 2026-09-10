import os
import datetime
import pytz
import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta

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

import os
import datetime
import pytz
import requests
import pandas as pd
import yfinance as yf

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
    
    # 1. อ่านรายชื่อหุ้นจากไฟล์ tickers.txt
    try:
        with open("tickers.txt", "r") as file:
            symbols = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("Error: ไม่พบไฟล์ tickers.txt บน GitHub")
        return

    # 2. เติม .BK ต่อท้ายชื่อหุ้นสำหรับตลาดไทย
    tickers = [f"{sym}.BK" for sym in symbols]

    print(f"Total tickers loaded: {len(tickers)} symbols")
    print(f"Downloading data...")
    
    # ดึงข้อมูลย้อนหลัง 1 ปี แบบกลุ่ม (Bulk Download)
    data = yf.download(tickers, period="1y", group_by='ticker', threads=True, progress=False)
    
    passed_stocks = []
    
    for ticker in tickers:
        try:
            if ticker not in data: 
                continue
            
            df = data[ticker].copy()
            df = df.dropna()
            
            # ต้องมีข้อมูลอย่างน้อย 200 วันทำการ เพื่อคำนวณเส้น EMA 200
            if len(df) < 200: 
                continue
              
            # แปลงชื่อคอลัมน์ให้เป็นตัวพิมพ์ใหญ่ (ป้องกันปัญหาระบบ MultiIndex)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(col).capitalize() for col in df.columns]

            # 3. คำนวณตัวชี้วัดตามเงื่อนไข Trend Following
            df["EMA_50"] = df["Close"].ewm(span=50).mean()
            df["EMA_200"] = df["Close"].ewm(span=200).mean()
            df["Vol_SMA20"] = df["Volume"].rolling(20).mean()
              
            # ดึงข้อมูลของวันล่าสุด (-1) มาตรวจสอบเงื่อนไข
            last_close = df["Close"].iloc[-1]
            last_ema50 = df["EMA_50"].iloc[-1]
            last_ema200 = df["EMA_200"].iloc[-1]
            last_vol = df["Volume"].iloc[-1]
            last_vol_sma20 = df["Vol_SMA20"].iloc[-1]
              
            # 4. เงื่อนไข Trend Following ต้นรอบ
            is_uptrend = (last_close > last_ema50) and (last_ema50 > last_ema200)
            is_near_support = (last_close >= last_ema50 * 0.98) and (last_close <= last_ema50 * 1.05) # ย่อมาแตะหรืออยู่ใกล้เส้น EMA 50
            is_volume_spike = last_vol > (last_vol_sma20 * 1.5) # วอลุ่มพุ่งทะลักกว่าค่าเฉลี่ย 20 วัน 1.5 เท่า
              
            if is_uptrend and is_near_support and is_volume_spike:
                display_name = ticker.replace(".BK", "")
                passed_stocks.append({
                    'ticker': display_name,
                    'price': last_close,
                    'ema50': last_ema50
                })
              
        except Exception as e:
            continue
            
    # ตั้งค่าโซนเวลาประเทศไทย
    tz = pytz.timezone('Asia/Bangkok')
    time_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    # 5. จัดรูปแบบข้อความส่งเข้า LINE
    if passed_stocks:
        results_text = [f"🟢 {s['ticker']} | ฿{s['price']:.2f} | EMA50: ฿{s['ema50']:.2f}" for s in passed_stocks]
        msg = f"🚀 หุ้น Trend Following ต้นรอบ\n({time_str})\n\n" + "\n".join(results_text)
        send_line_message(msg)
    else:
        msg = f"📉 หุ้น Trend Following ต้นรอบ\n({time_str})\n\nรอบนี้ยังไม่มีหุ้นตัวใดเข้าเงื่อนไข"
        send_line_message(msg)
        
    print("Done!")

if __name__ == "__main__":
    main()
