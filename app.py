import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser
import numpy as np
from scipy.stats import norm

# 1. 금액 변환 함수
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

# 2. 상승 확률 계산 (보수적 통계 모델)
def calculate_up_probability(data):
    try:
        returns = np.log(data['Close'] / data['Close'].shift(1))
        volatility = returns.std()
        last_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        z_score = (last_price - prev_price) / (prev_price * volatility)
        prob = norm.cdf(z_score) * 100
        return min(max(prob, 10), 90) # 10~90% 사이 제한
    except:
        return 50.0

st.set_page_config(page_title="민구의 AI 주식 분석기", layout="wide")

# 타이틀 강조
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🤖 민구의 AI 주식 분석기</h1>", unsafe_allow_html=True)
st.write("---")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("AI 분석 시작"):
    with st.spinner('민구 님이 설정한 AI가 데이터를 수집 중입니다...'):
        try:
            # 종목 코드 검색
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 데이터 로드 (최근 1개월)
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    last_price = float(data['Close'].iloc[-1])
                    last_vol = float(data['Volume'].iloc[-1])
                    val_billion = (last_price * last_vol) / 100000000
                    up_prob = calculate_up_probability(data)

                    # 지표 출력 (4열 배치)
                    st.subheader(f"✅ {target_name} AI 분석 결과")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("현재가", f"{int(last_price):,}원")
                    m2.metric("거래량", f"{int(last_vol):,}주")
                    m3.metric("거래대금", format_korean_currency(val_billion))
                    m4.metric("오늘의 상승 확률", f"{up_prob:.1f}%")

                    st.divider()

                    # 일정 및 뉴스 (오류 방지 처리)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📅 향후 1주일 주요 일정")
                        try:
                            plan_url = f"https://news.google.com/rss/search?q={target_name}+(일정+OR+공시+OR+발표)&hl=ko&gl=KR&ceid=KR:ko"
                            plan_feed = feedparser.parse(plan_url)
                            if plan_feed.entries:
                                for entry in plan_feed.entries[:5]:
                                    st.write(f"📍 {entry.title.rsplit(' - ', 1)[0]}")
                            else:
                                st.write("확인된 일정이 없습니다.")
                        except:
                            st.write("일정 데이터를 가져오지 못했습니다. 잠시 후 새로고침해 주세요.")
                        st.link_button("🔍 DART 공시 상세 확인", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                    with col2:
                        st.subheader("📰 최신 주요 뉴스")
                        try:
                            news_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                            news_feed = feedparser.parse(news_url)
                            for entry in news_feed.entries[:5]:
                                st.write(f"• [{entry.title.rsplit(' - ', 1)[0]}]({entry.link})")
                        except:
                            st.write("뉴스 데이터를 일시적으로 불러올 수 없습니다.")

                else:
                    st.warning("주가 데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error("분석 엔진에 일시적인 정체가 발생했습니다. 다시 눌러주세요.")
