import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import feedparser

# 앱 설정
st.set_page_config(page_title="민구의 데이터 분석기", layout="wide")
st.title("📊 민구의 주식 수급/데이터 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("데이터 분석 시작"):
    with st.spinner('거래대금 및 수급 데이터를 계산 중...'):
        try:
            # 1. 종목 찾기 및 데이터 로드
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                data = yf.download(full_ticker, period="3mo", progress=False).dropna()
                
                if not data.empty:
                    # --- [신규 추가] 수급 및 거래대금 계산 ---
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    # 거래대금 계산 (종가 * 거래량) -> 억 단위로 변환
                    trading_value_won = last_price * last_volume
                    trading_value_billion = trading_value_won / 100000000
                    
                    # 최근 5일 평균 거래량 대비 비율
                    avg_vol_5d = data['Volume'].tail(5).mean()
                    vol_ratio = (last_volume / avg_vol_5d) * 100

                    # 화면 출력 (메트릭)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("현재가", f"{int(last_price):,}원")
                    with col2:
                        st.metric("오늘 거래대금", f"{trading_value_billion:.1f} 억")
                    with col3:
                        st.metric("5일 평균 대비 거래량", f"{vol_ratio:.1f}%")

                    # 2. AI 상승 확률 예측
                    if len(data) >= 20:
                        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
                        features = ['Open', 'High', 'Low', 'Close', 'Volume']
                        train_df = data.dropna()
                        model = RandomForestClassifier(n_estimators=100, random_state=1)
                        model.fit(train_df[features].iloc[:-1], train_df['Target'].iloc[:-1])
                        prob = model.predict_proba(train_df[features].tail(1))[0][1]
                        st.success(f"AI 분석 결과: 내일 상승 확률 {prob*100:.1f}%")
                    
                    st.divider()

                # 3. 뉴스 파트 (RSS 방식 - 가장 안정적)
                st.subheader(f"📰 {target_name} 실시간 주요 뉴스")
                rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                feed = feedparser.parse(rss_url)

                if feed.entries:
                    for entry in feed.entries[:15]:
                        title = entry.title
                        link = entry.link
                        parts = title.rsplit(' - ', 1)
                        clean_title = parts[0]
                        media = parts[1] if len(parts) > 1 else "뉴스"
                        st.write(f"• [{media}] [{clean_title}](%s)" % link)
                else:
                    st.info("최근 일주일간 뉴스가 없습니다.")
                    
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생")
