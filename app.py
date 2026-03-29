import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 앱 설정
st.set_page_config(page_title="민구의 AI 분석기", layout="wide")
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("분석할 종목명을 입력하세요", "삼성전자")

if st.button("분석 시작"):
    with st.spinner('일주일치 뉴스를 샅샅이 긁어오는 중...'):
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

                # 2. 뉴스 파트 (네이버 전체 뉴스 검색 방식)
                st.subheader(f"📰 {target_name} 일주일치 뉴스 리스트")
                
                # 최신순 정렬(sort=1)로 일주일치 뉴스 수집
                count = 0
                for start in [1, 11, 21]: # 총 30개 뉴스 확인
                    search_url = f"https://search.naver.com/search.naver?where=news&query={target_name}&sort=1&start={start}"
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                    resp = requests.get(search_url, headers=headers)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    news_items = soup.select('ul.list_news > li')

                    if not news_items: break

                    for item in news_items:
                        try:
                            # 언론사
                            press = item.select_one('a.info.press').text.replace('언론사 선정', '').strip()
                            # 제목 및 링크
                            title_anchor = item.select_one('a.news_tit')
                            title = title_anchor.text
                            link = title_anchor['href']
                            # 날짜
                            date = item.select_one('span.info').text
                            
                            st.write(f"• [{press}] [{title}](%s) <span style='color:gray; font-size:12px;'>({date})</span>" % link, unsafe_allow_html=True)
                            count += 1
                        except:
                            continue
                
                if count == 0:
                    st.info("뉴스를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.")
                    
        except Exception as e:
            st.error("데이터를 불러오는 중 오류가 발생했습니다.")
