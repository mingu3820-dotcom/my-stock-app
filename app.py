import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser
from datetime import datetime, timedelta

# 1. 한글 금액 변환 함수 (5조 2,479억 형식)
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

# 앱 설정
st.set_page_config(page_title="민구의 주식 분석기", layout="wide")
st.title("📊 삼성전자 수급 및 1주일 주요 일정")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("데이터 분석 시작"):
    with st.spinner('실시간 수급과 일정을 분석 중입니다...'):
        try:
            # 1. 종목 코드 찾기
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 2. 주가 데이터 가져오기
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    # [지표 계산]
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    trading_value_billion = (last_price * last_volume) / 100000000
                    korean_value = format_korean_currency(trading_value_billion)

                    # 상단 수급 출력
                    st.subheader(f"✅ {target_name} 수급 팩트")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("현재가", f"{int(last_price):,}원")
                    c2.metric("오늘 거래량", f"{int(last_volume):,}주")
                    c3.metric("오늘 거래대금", korean_value)
                    
                    st.divider()

                    # 3. 1주일 일정 & 뉴스 (두 열로 배치)
                    col_plan, col_news = st.columns(2)

                    with col_plan:
                        st.subheader("📅 향후 1주일 주요 일정/공시")
                        # '일정', '발표', '공시' 키워드로 뉴스에서 일정 정보를 긁어옴
                        plan_query = f"{target_name}+(일정+OR+발표+OR+공시+OR+배당)"
                        plan_url = f"https://news.google.com/rss/search?q={plan_query}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        plan_feed = feedparser.parse(plan_url)
                        
                        if plan_feed.entries:
                            for entry in plan_feed.entries[:10]:
                                # 제목에서 언론사 제거 후 깔끔하게 출력
                                title = entry.title.rsplit(' - ', 1)[0]
                                st.write(f"📍 {title}")
                        else:
                            st.write("확인된 일정이 없습니다.")
                        
                        st.write("---")
                        st.link_button("🔍 DART 전자공시 직접 확인", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                    with col_news:
                        st.subheader("📰 최신 주요 뉴스")
                        rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        feed = feedparser.parse(rss_url)
                        if feed.entries:
                            for entry in feed.entries[:10]:
                                title = entry.title.rsplit(' - ', 1)[0]
                                st.write(f"• [{title}]({entry.link})")

                else:
                    st.warning("데이터를 불러오지 못했습니다.")

        except Exception:
            st.error("오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
