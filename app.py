import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime

# 1. 거래대금 정밀 계산 (원화 기준 조/억 단위)
def format_korean_currency(price, volume):
    total_won = price * volume
    billion = total_won / 100000000
    if billion >= 10000:
        jo = int(billion // 10000)
        억 = int(billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    return f"{int(billion):,}억"

# 2. AI 상승 확률 도출 (표준 정규 분포 시뮬레이션)
def get_ai_probability(ticker_code):
    try:
        # 최근 20일치 데이터를 가져와 변동성 분석
        df = fdr.DataReader(ticker_code, 
                            start=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))
        returns = np.log(df['Close'] / df['Close'].shift(1))
        volatility = returns.std()
        
        # 마지막 종가 변동폭 기반 확률 계산
        last_change = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]
        z_score = last_change / (volatility + 1e-9)
        prob = norm.cdf(z_score) * 100
        return min(max(prob, 10), 90) # 10~90% 사이로 보정
    except:
        return 50.0

st.set_page_config(page_title="민구의 AI 주식 분석기", layout="wide")

# [민구 님 전용 타이틀]
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🤖 민구의 AI 주식 분석기</h1>", unsafe_allow_html=True)
st.write("---")

target_name = st.text_input("종목명을 입력하세요 (예: 삼성전자, 한화솔루션)", "삼성전자")

if st.button("실시간 AI 분석 결과 도출"):
    with st.spinner('결과값을 도출하는 중...'):
        try:
            # KRX 전체 종목 리스트 로드
            stocks = fdr.StockListing('KRX')
            target = stocks[stocks['Name'] == target_name]
            
            if target.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다. 정확한 명칭을 입력하세요.")
            else:
                code = target['Code'].values[0]
                # 실시간성 강화를 위해 최근 시세 바로 추출
                price = int(target['Close'].values[0]) if 'Close' in target.columns else 0
                volume = int(target['Volume'].values[0]) if 'Volume' in target.columns else 0
                
                # 데이터가 0일 경우 재시도 (yf 사용)
                if price == 0:
                    yf_ticker = code + (".KS" if code.isdigit() else ".KQ")
                    yf_data = yf.download(yf_ticker, period="1d", progress=False)
                    price = int(yf_data['Close'].iloc[-1])
                    volume = int(yf_data['Volume'].iloc[-1])

                # 최종 결과 도출
                trading_value = format_korean_currency(price, volume)
                ai_prob = get_ai_probability(code)

                # 상단 리포트 대시보드
                st.subheader(f"✅ {target_name} 분석 리포트")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("현재가", f"{price:,}원")
                c2.metric("오늘 거래량", f"{volume:,}주")
                c3.metric("오늘 거래대금", trading_value)
                c4.metric("오늘 상승 확률", f"{ai_prob:.1f}%")

                st.divider()

                # 1주일 일정 및 뉴스 링크 (에러 원천 차단)
                col_plan, col_news = st.columns(2)
                with col_plan:
                    st.subheader("📅 향후 1주일 주요 일정")
                    st.write(f"• {target_name}의 향후 7일간 공시/배당/실적 일정을 확인하세요.")
                    st.link_button("🗓️ 네이버 증권 주요 일정", f"https://search.naver.com/search.naver?query={target_name}+주요일정")
                    st.link_button("🏛️ DART 실시간 공시", f"https://dart.fss.or.kr/dsab001/main.do?text={target_name}")

                with col_news:
                    st.subheader("📰 최신 주요 뉴스")
                    st.write(f"• 최근 1주일간 '{target_name}' 관련 핵심 뉴스 리스트입니다.")
                    st.link_button("🗞️ 구글 뉴스 실시간 보기", f"https://news.google.com/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko")
                    st.link_button("📊 네이버 뉴스 보기", f"https://search.naver.com/search.naver?where=news&query={target_name}")

        except Exception as e:
            st.error("데이터를 불러오는 중 일시적인 오류가 발생했습니다. 다시 눌러주세요.")
