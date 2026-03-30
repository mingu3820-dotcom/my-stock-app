import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser
from datetime import datetime, timedelta

# 금액 단위 변환 함수 (5조 2,479억 형식)
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

st.set_page_config(page_title="민구의 주식 팩트 체크", layout="wide")
st.title("📊 민구의 주식 수급 & 일정 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("데이터 분석 시작"):
    with st.spinner('데이터를 불러오는 중...'):
        try:
            # 1. 종목 코드 찾기
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 2. 주가 데이터 가져오기 (가벼운 1개월치)
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    # [수급 팩트 계산]
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    trading_value_billion = (last_price * last_volume) / 100000000
                    korean_value = format_korean_currency(trading_value_billion)

                    # 화면 상단 출력
                    st.subheader(f"✅ {target_name} 수급 현황")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("현재가", f"{int(last_price):,}원")
                    c2.metric("오늘 거래량", f"{int(last_volume):,}주")
                    c3.metric("오늘 거래대금", korean_value)
                    
                    st.divider()

                    # 3. 뉴스 & 1주일 일정 (두 열로 배치)
                    col_news, col_plan = st.columns(2)

                    with col_news:
                        st.subheader("📰 최신 주요 뉴스")
                        rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        feed = feedparser.parse(rss_url)
                        if feed.entries:
                            for entry in feed.entries[:8]:
                                title = entry.title.rsplit(' - ', 1)[0]
                                st.write(f"• [{title}]({entry.link})")
                        else:
                            st.write("최근 뉴스가 없습니다.")

                    with col_plan:
                        st.subheader("📅 1주일 주요 일정/공시")
                        # '일정'과 '공시' 키워드로 뉴스에서 정보를 추출하여 일정처럼 보여줌
                        plan_url = f"https://news.google.com/rss/search?q={target_name}+(일정+OR+공시)+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        plan_feed = feedparser.parse(plan_url)
                        
                        st.info("💡 향후 1주일간의 주요 공시 및 리포트 일정입니다.")
                        if plan_feed.entries:
                            for entry in plan_feed.entries[:5]:
                                title = entry.title.rsplit(' - ', 1)[0]
                                st.write(f"📍 {title}")
                        
                        st.write("---")
                        # 가장 확실한 공식 일정 링크 버튼
                        st.link_button(f"🔍 {target_name} 상세 공시(DART) 바로가기", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                else:
                    st.warning("주가 데이터를 가져오지 못했습니다.")

        except Exception as e:
            st.error("서버 연결이 원활하지 않습니다. 잠시 후 다시 시도해 주세요.")
