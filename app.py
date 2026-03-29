import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
from GoogleNews import GoogleNews
import pandas as pd

# 앱 화면 설정
st.set_page_config(page_title="민구의 AI 분석기")
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("종목명을 정확히 입력하세요", "삼성전자")

if st.button("분석 시작"):
    with st.spinner('AI가 데이터를 분석 중입니다...'):
        try:
            # 1. 종목 코드 찾기
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 2. 데이터 가져오기
                data = yf.download(full_ticker, period="3mo", progress=False).dropna()
                
                if len(data) < 20:
                    st.warning("데이터가 너무 적어 분석이 불가능합니다.")
                else:
                    # 3. AI 학습 및 예측
                    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
                    features = ['Open', 'High', 'Low', 'Close', 'Volume']
                    train_df = data.dropna()
                    
                    X = train_df[features].iloc[:-1]
                    y = train_df['Target'].iloc[:-1]
                    
                    model = RandomForestClassifier(n_estimators=100, random_state=1)
                    model.fit(X, y)
                    
                    prob = model.predict_proba(train_df[features].tail(1))[0][1]

                    # 4. 결과 출력
                    st.success("분석 완료!")
                    st.metric(label=f"{target_name} 내일 상승 확률", value=f"{prob*100:.1f}%")

                    # 5. 구글 뉴스
                    st.subheader(f"📰 {target_name} 최신 뉴스")
                    try:
                        gn = GoogleNews(lang='ko', period='7d')
                        gn.search(target_name)
                        news_results = gn.results()
                        if news_results:
                            for i, item in enumerate(news_results[:10], 1):
                                st.write(f"{i}. [{item.get('media', '미확인')}] {item.get('title')}")
                        else:
                            st.write("최근 뉴스가 없습니다.")
                    except:
                        st.write("뉴스 정보를 불러오지 못했습니다.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
