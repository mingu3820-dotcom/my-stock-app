import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 앱 설정
st.set_page_config(page_title="민구의 AI 분석기", layout="wide")
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("분석할 종목명을 입력하세요", "삼성전자")

if st.button("분석 시작"):
    with st.spinner('일주일치 뉴스를 샅샅이 뒤지는 중입니다...'):
        try:
            # 1. 주가 분석 파트
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                data = yf.download(full_ticker, period="3mo", progress=False).dropna()
                
                if len(data) >= 20:
                    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
                    features = ['Open', 'High', 'Low', 'Close', 'Volume']
                    train_df = data.dropna()
                    model = RandomForestClassifier(n_estimators=100, random_state=1)
                    model.fit(train_df[features].iloc[:-1], train_df['Target'].iloc[:-1])
                    prob = model.predict_proba(train_df[features].tail(1))[0][1]
                    
                    st.success("AI 분석 완료")
                    st.metric(label=f"{target_name} 내일 상승 예측 확률", value=f"{prob*100:.1f}%")
                
                st.divider()

                # 2. 뉴스 파트 (여러 페이지 수집)
                st.subheader(f"📰 {target_name} 최신 증권 뉴스 (최대 3페이지)")
                
                count = 0
                for page in range(1, 4): # 1페이지부터 3페이지까지 수집
                    news_url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page={page}"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(news_url, headers=headers)
                    resp.encoding = 'euc-kr'
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    titles = soup.select('td.title > a')
                    infos = soup.select('td.info')
                    dates = soup.select('td.date')

                    if not titles:
                        break

                    for i in range(len(titles)):
                        title_text = titles[i].text.strip()
                        press_text = infos[i].text.strip()
                        date_text = dates[i].text.strip()
                        link = "https://finance.naver.com" + titles[i]['href']
                        
                        st.write(f"• [{press_text}] [{title_text}](%s) <span style='color:gray; font-size:12px;'>{date_text}</span>" % link, unsafe_allow_html=True)
                        count += 1
                
                if count == 0:
                    st.info("최근 네이버 증권에 올라온 뉴스가 없습니다.")
                    
        except Exception as e:
            st.error("데이터를 불러오는 중 오류가 발생했습니다.")
