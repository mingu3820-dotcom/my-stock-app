import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser
import numpy as np
from scipy.stats import norm

# 1. 한글 금액 변환 함수
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

# 2. 상승 확률 계산 함수 (통계적 시뮬레이션)
def calculate_up_probability(data):
    # 최근 20일 수익률 기반 변동성 계산
    returns = np.log(data['Close'] / data['Close'].shift(1))
    volatility = returns.std()
    last_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    
    # 전일 대비 변동폭을 정규분포 상의 확률로 변환
    z_score = (last_price - prev_price) / (prev_price * volatility)
    prob = norm.cdf(z_score) * 100
    return min(max(prob, 5), 95)  # 5% ~ 95% 사이로 제한

# 앱 설정
st.set_page_config(page_title="민구의 AI 주식 분석기", layout="wide")
st.title("🤖 민구의 AI 주식 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("AI 분석 시작"):
    with st.spinner('AI가 수급과 확률을 계산 중입니다...'):
        try:
            # 종목 코드 찾기
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 데이터 가져오기 (최근 1개월)
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    trading_value_billion = (last_price * last_volume) / 100000000
                    
                    # AI 확률 계산
                    up_prob = calculate_up_probability(data)

                    # 결과 출력
                    st.subheader(f"✅ {target_name} AI 분석 리포트")
                    
                    # 주요 지표 4개 배치
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("현재가", f"{int(last_price):,}원")
                    m2.metric("거래량", f"{int(last_volume):,}주")
                    m3.metric("거래대금", format_korean_currency(trading_value_billion))
                    m4.metric("오늘의 상승 확률", f"{up_prob:.1f}%")

                    st.divider()

                    # 일정 및 뉴스
                    col_plan, col_news = st.columns(2)

                    with col_plan:
                        st.subheader("📅 향후 1주일 주요 일정")
                        plan_query = f"{target_name}+(일정+OR+발표+OR+공시+OR+배당)"
                        plan_url = f"https://news.google.com/rss/search?q={plan_query}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        plan_feed = feedparser.parse(plan_url)
                        
                        if plan_feed.entries:
                            for entry in plan_feed.entries[:8]:
                                st.write(f"📍 {entry.title.rsplit(' - ', 1)[0]}")
                        else:
                            st.write("확인된 일정이 없습니다.")
                        
                        st.link_button("🔍 DART 공시 상세 확인", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                    with col_news:
                        st.subheader("📰 최신 주요 뉴스")
                        rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                        feed = feedparser.parse(rss_url)
                        for entry in feed.entries[:8]:
                            st.write(f"• [{entry.title.rsplit(' - ', 1)[0]}]({entry.link})")

                else:
                    st.warning("데이터 로드 실패")

        except Exception:
            st.error("분석 중 오류가 발생했습니다. 잠시 후 다시 시도하세요.")
