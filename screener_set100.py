import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime
import pytz # เพิ่มไลบรารีจัดการเวลา

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
    print("Fetching SET & MAI tickers...")
    
    symbols = [
        "ADVANC", "AMATA", "AOT", "AP", "AWC", "BAM", "BANPU", "BBL", "BCH", "BCP", 
        "BDMS", "BEM", "BGRIM", "BH", "BJC", "BLA", "BTS", "CBG", "CENTEL", "CHG", 
        "CK", "COM7", "CPALL", "CPAXT", "CPF", "CPN", "CRC", "DELTA", "EA", "EGCO", 
        "FORTH", "GLOBAL", "GPSC", "GULF", "HANA", "HMPRO", "ICHI", "INTUCH", "IVL", 
        "JMART", "JMT", "KBANK", "KCE", "KKP", "KTB", "KTC", "LH", "MEGA", "MINT", 
        "MTC", "OR", "OSP", "PLANB", "PRM", "PTG", "PTT", "PTTEP", "PTTGC", "QH", 
        "RATCH", "SAWAD", "SCB", "SCC", "SCGP", "SIRI", "SPALI", "SPRC", "STA", 
        "TASCO", "TCAP", "TISCO", "TOP", "TRUE", "TTB", "TU", "WHA",
        "COCOCO", "FORTH", "PSP", "TGE", "MASTER", "BELT", "SAFE", "SNP", "MEDEE"
    ]
    
    tickers = [f"{sym}.BK" for sym in symbols]

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
            
            last = df.iloc[-1]
            close_price = last['Close']
            ema20 = last['EMA_20']
            ema50 = last['EMA_50']
            ema200 = last['EMA_200']
            
            # 1. เงื่อนไขเทรนด์ขาขึ้น
            cond_trend = (close_price > ema20) and (ema20 > ema50) and (ema50 > ema200)
            
            if cond_trend:
                # คำนวณแรงผลัก (% ห่างจาก EMA200)
                pct_above_ema200 = ((close_price - ema200) / ema200) * 100
                
                # 2. กรองเฉพาะหุ้นที่มีแรงผลักอยู่ในช่วง 3% ถึง 12% เท่านั้น 
                if 3.0 <= pct_above_ema200 <= 12.0:
                    display_name = ticker.replace(".BK", "")
                    passed_stocks.append({
                        'ticker': display_name,
                        'price': close_price,
                        'power': pct_above_ema200
                    })
                
        except Exception as e:
            continue
            
    # เรียงลำดับตามแรงผลักจากมากไปน้อย (เอาสูงสุดไม่เกิน 20 ตัว)
    top_stocks = sorted(passed_stocks, key=lambda x: x['power'], reverse=True)[:20]
    
    # ปรับเวลาให้เป็นโซนเวลาประเทศไทยเสมอ (รองรับการรันบนเซิร์ฟเวอร์ GitHub ที่เป็น UTC)
    tz = pytz.timezone('Asia/Bangkok')
    time_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
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
