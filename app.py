import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import feedparser

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
st.title("📊 민구의 주식 수급/데이터 분석기")

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
                
                # 2. 데이터 가져오기 (메모리 보호를 위해 6개월치만 사용)
                data = yf.download(full_ticker, period="6mo", progress=False)
                data = data.dropna()
                
                if not data.empty:
                    # [데이터 계산]
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    trading_value_billion = (last_price * last_volume) / 100000000
                    
                    # 한글 단위 변환
                    korean_value = format_korean_currency(trading_value_billion)
                    
                    # 5일 평균 거래량 대비 비율
                    avg_vol_5d = data['Volume'].tail(5).mean()
                    vol_ratio = (last_volume / avg_vol_5d) * 100

                    # 상단 지표 출력
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("현재가", f"{int(last_price):,}원")
                    with col2:
                        st.metric("오늘 거래대금", korean_value)
                    with col3:
                        st.metric("5일 평균 대비 수급", f"{vol_ratio:.1f}%")

                    st.divider()

                    # 3. AI 분석 파트 (충돌 방지 최적화)
                    if len(data) > 20:
                        # 데이터 복사 및 타겟 생성
                        df_ai = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                        df_ai['Target'] = (df_ai['Close'].shift(-1) > df_ai['Close']).astype(int)
                        
                        train_data = df_ai.dropna()
                        X = train_data[['Open', 'High', 'Low', 'Close', 'Volume']].iloc[:-1]
                        y = train_data['Target'].iloc[:-1]
                        
                        # 모델 학습 (속도를 위해 가볍게 설정)
                        model = RandomForestClassifier(n_estimators=30, random_state=42)
                        model.fit(X, y)
                        
                        # 마지막 날 데이터로 예측
                        last_row = train_data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(1)
                        prob = model.predict_proba(last_row)[0][1]
                        
                        st.success(f"📈 AI 분석 결과: 내일 상승 예측 확률 **{prob*100:.1f}%**")
                    
                    # 4. 실시간 뉴스
                    st.subheader(f"📰 {target_name} 실시간 주요 뉴스")
                    rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                    feed = feedparser.parse(rss_url)

                    if feed.entries:
                        for entry in feed.entries[:8]:
                            title = entry.title.rsplit(' - ', 1)[0]
                            st.write(f"• {title}")
                else:
                    st.warning("주가 데이터를 가져올 수 없습니다.")

        except Exception as e:
            st.error("데이터 처리 중 일시적인 지연이 발생했습니다. 다시 한번 [분석 시작]을 눌러주세요.")
