import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
from GoogleNews import GoogleNews
import pandas as pd

# 앱 화면 설정
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("분석 시작"):
    try:
        # 주가 데이터 가져오기
        df_all = fdr.StockListing('KRX')
        ticker = df_all[df_all['Name'] == target_name]['Code'].values[0]
        full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
        data = yf.download(full_ticker, period="3mo", progress=False).dropna()
        
        # AI 학습 및 예측
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
        features = ['Open', 'High', 'Low', 'Close', 'Volume']
        train_df = data.dropna()
        model = RandomForestClassifier(n_estimators=100, random_state=1)
        model.fit(train_df[features].iloc[:-1], train_df['Target'].iloc[:-1])
        prob = model.predict_proba(data[features].tail(1))[0][1]

        st.metric(label=f"{target_name} 내일 상승 확률", value=f"{prob*100:.1f}%")

        # 구글 뉴스 10개
        st.subheader(f"📰 {target_name} 최신 뉴스")
        gn = GoogleNews(lang='ko', period='7d')
        gn.search(target_name)
        for i, item in enumerate(gn.results()[:10], 1):
            st.write(f"{i}. [{item.get('media')}] {item.get('title')}")
            
    except:
        st.error("종목명을 정확히 입력해주세요.")
