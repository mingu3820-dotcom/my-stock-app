import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from scipy.stats import norm
import feedparser
import datetime

# 1. 거래대금 정확한 변환 함수
def format_korean_currency(value_won):
    billion = value_won / 100000000
    if billion >= 10000:
        jo = int(billion // 10000)
        억 = int(billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    return f"{int(billion):,}억"

# 2. 상승 확률 계산 (보수적 통계 모델)
def calculate_up_probability(data):
    try:
        returns = np.log(data['Close'] / data['Close'].shift(1))
        volatility = returns.std()
        last_price = float(data['Close'].iloc[-1])
        prev_price = float(data['Close'].iloc[-2])
        z_score = (last_price - prev_price) / (prev_price * volatility + 1e-9)
        prob = norm.cdf(z_score) * 100
        return min(max(prob, 15), 85)
    except:
        return 50.0

st.set_page_config(page_title="민구의 AI 주식 분석기", layout="wide")

# [민구 이름 강조 타이틀]
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🤖 민구의 AI 주식 분석기</h1>", unsafe_allow_html=True)
st.write("---")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("AI 분석 시작"):
    with st.spinner('민구가 설정한 AI가 정밀 분석 중...'):
        try:
            # 종목 코드 검색
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 데이터 수집
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    last_price = float(data['Close'].iloc[-1])
                    last_vol = float(data['Volume'].iloc[-1])
                    # 거래대금 팩트 체크 (종가 * 거래량)
                    trading_value_won = last_price * last_vol
                    korean_value = format_korean_currency(trading_value_won)
                    up_prob = calculate_up_probability(data)

                    # 결과 리포트 (4열)
                    st.subheader(f"✅ {target_name} AI 분석 결과")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("현재가", f"{int(last_price):,}원")
                    m2.metric("오늘 거래량", f"{int(last_vol):,}주")
                    m3.metric("오늘 거래대금", korean_value)
                    m4.metric("오늘 상승 확률", f"{up_prob:.1f}%")

                    st.divider()

                    # 뉴스/일정 (오류 방지용 try-except 개별 적용)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📅 향후 1주일 주요 일정")
                        try:
                            p_url = f"https://news.google.com/rss/search?q={target_name}+(일정+OR+공시+OR+배당)&hl=ko&gl=KR&ceid=KR:ko"
                            p_feed = feedparser.parse(p_url)
                            if p_feed.entries:
                                for entry in p_feed.entries[:5]:
                                    st.write(f"📍 {entry.title.rsplit(' - ', 1)[0]}")
                            else: st.write("확인된 일정이 없습니다.")
                        except: st.write("일정 데이터를 일시적으로 불러올 수 없습니다.")
                        st.link_button("🔍 DART 공시 상세 확인", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                    with col2:
                        st.subheader("📰 최신 주요 뉴스")
                        try:
                            n_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                            n_feed = feedparser.parse(n_url)
                            for entry in n_feed.entries[:5]:
                                st.write(f"• [{entry.title.rsplit(' - ', 1)[0]}]({entry.link})")
                        except: st.write("뉴스 데이터를 가져오는 중 지연이 발생했습니다.")
                else:
                    st.warning("데이터가 아직 업데이트되지 않았습니다.")
        except Exception:
            st.error("분석 엔진 연결에 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.")
