import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser

def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

st.set_page_config(page_title="민구의 주식 분석기", layout="wide")
st.title("📊 민구의 주식 수급 & 뉴스")

target_name = st.text_input("종목명 입력", "삼성전자")

if st.button("분석 시작"):
    try:
        df_all = fdr.StockListing('KRX')
        ticker = df_all[df_all['Name'] == target_name]['Code'].values[0]
        full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
        
        data = yf.download(full_ticker, period="1mo", progress=False).dropna()
        
        if not data.empty:
            last_price = float(data['Close'].iloc[-1])
            last_vol = float(data['Volume'].iloc[-1])
            val_billion = (last_price * last_vol) / 100000000
            
            st.subheader(f"✅ {target_name} 팩트 체크")
            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", f"{int(last_price):,}원")
            col2.metric("거래량", f"{int(last_vol):,}주")
            col3.metric("거래대금", format_korean_currency(val_billion))
            
            st.divider()
            st.subheader("📰 최신 뉴스")
            rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:8]:
                st.write(f"• [{entry.title.rsplit(' - ', 1)[0]}]({entry.link})")
    except:
        st.error("종목명을 확인하시거나 잠시 후 다시 시도해 주세요.")
