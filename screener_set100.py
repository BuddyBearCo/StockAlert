import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import os
import datetime

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
    print("Fetching SET100 tickers...")
    # รายชื่อหุ้นใหญ่ในไทย 100 ตัว (SET100)
    set100_symbols = [
        "ADVANC", "AMATA", "AOT", "AP", "AWC", "BAM", "BANPU", "BBL", "BCH", "BCP", 
        "BCPG", "BDMS", "BEM", "BGRIM", "BH", "BJC", "BLA", "BTS", "CBG", "CENTEL", 
        "CHG", "CK", "CKP", "COM7", "CPALL", "CPAXT", "CPF", "CPN", "CRC", "DELTA", 
        "EA", "EGCO", "EPG", "ERW", "FORTH", "GLOBAL", "GPSC", "GULF", "HANA", "HMPRO", 
        "ICHI", "INTUCH", "IRPC", "IVL", "JAS", "JMART", "JMT", "KBANK", "KCE", "KEX", 
        "KKP", "KTB", "KTC", "LH", "MEGA", "MINT", "MTC", "OR", "ORI", "OSP", 
        "PLANB", "PRM", "PSH", "PSL", "PTG", "PTT", "PTTEP", "PTTGC", "QH", "RATCH", 
        "RCL", "RS", "SAWAD", "SCB", "SCC", "SCCC", "SCGP", "SIRI", "SPALI", "SPRC", 
        "STA", "STEC", "SUPER", "TASCO", "TCAP", "THANI", "THCOM", "THG", "TISCO", "TKN", 
        "TOP", "TRUE", "TTB", "TU", "VGI", "WHA"
    ]
    
    # เติม .BK เพื่อให้ yfinance ดึงข้อมูลหุ้นไทยได้
    tickers = [f"{sym}.BK" for sym in set100_symbols]

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
            
            # เกณฑ์: Perfect Uptrend Alignment
            cond_trend = (close_price > ema20) and (ema20 > ema50) and (ema50 > ema200)
            
            if cond_trend:
                # คำนวณความแรงของเทรนด์: ราคาวิ่งห่างจากเส้น EMA200 ไปแล้วกี่เปอร์เซ็นต์
                pct_above_ema200 = ((close_price - ema200) / ema200) * 100
                display_name = ticker.replace(".BK", "") # ลบ .BK ออกเวลาส่งเข้า LINE
                
                passed_stocks.append({
                    'ticker': display_name,
                    'price': close_price,
                    'power': pct_above_ema200
                })
                
        except Exception as e:
            continue
            
    # เรียงลำดับตามพลังเทรนด์ (ความห่างจาก EMA200) จากมากไปน้อย เอาแค่ 15 อันดับแรก
    top_stocks = sorted(passed_stocks, key=lambda x: x['power'], reverse=True)[:15]
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if top_stocks:
        results_text = [f"🟢 {s['ticker']} | ฿{s['price']:.2f} | แรงผลัก: +{s['power']:.1f}%" for s in top_stocks]
        msg = f"🇹🇭 Top 15 หุ้นไทยขาขึ้น (SET100)\n({date_str})\n\n" + "\n".join(results_text)
        
        if len(passed_stocks) > 15:
            msg += f"\n\n*(คัดจากหุ้นขาขึ้นทั้งหมด {len(passed_stocks)} ตัว)*"
            
        send_line_message(msg)
    else:
        msg = f"📉 สแกนหุ้นไทย ({date_str})\n\nไม่มีหุ้นเข้าเกณฑ์ Perfect Uptrend ในวันนี้"
        send_line_message(msg)
        
    print("Done!")

if __name__ == "__main__":
    main()
