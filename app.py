import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser
from datetime import datetime, timedelta

# 한글 금액 변환 함수
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

# 앱 설정
st.set_page_config(page_title="민구의 데이터 분석기", layout="wide")
st.title("📊 민구의 주식 수급 & 일정 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("데이터 분석 시작"):
    with st.spinner('데이터를 분석 중입니다...'):
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
                    # [지표 계산]
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    # 거래대금 계산 (종가 * 거래량 / 1억)
                    trading_value_billion = (last_price * last_volume) / 100000000
                    korean_value = format_korean_currency(trading_value_billion)

                    # 3. 화면 상단 지표 출력
                    st.subheader(f"📈 {target_name} 실시간 수급 팩트")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("현재가", f"{int(last_price):,}원")
                    with col2:
                        st.metric("오늘 거래량", f"{int(last_volume):,}주")
                    with col3:
                        st.metric("오늘 거래대금", korean_value)

                    st.divider()

                    # 4. 향후 1주일 일정 및 관련 뉴스
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.subheader(f"📅 {target_name} 향후 1주일 일정")
                        # 구글 검색 결과 기반 일정 링크 제공 (가장 확실한 방법)
                        today = datetime.now().strftime('%Y-%m-%d')
                        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                        st.info(f"기간: {today} ~ {next_week}")
                        
                        st.write("• 실시간 공시/일정 확인")
                        st.link_button(f"🔗 {target_name} 공시 확인 (DART)", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")
                        st.link_button(f"🗓️ 증권사 리포트/일정 보기", f"https://search.naver.com/search.naver?query={target_name}+주요일정")

                    with col_b:
                        st.subheader(f"📰 {target_name} 최신 뉴스")
                        rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        feed = feedparser.parse(rss_url)
                        if feed.entries:
                            for entry in feed.entries[:8]:
                                title = entry.title.rsplit(' - ', 1)[0]
                                st.write(f"• [{title}](%s)" % entry.link)
                        else:
                            st.write("최근 뉴스가 없습니다.")
                else:
                    st.warning("데이터를 가져오지 못했습니다.")

        except Exception as e:
            st.error("분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
