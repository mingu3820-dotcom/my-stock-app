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

# 허용할 언론사 (민구 님 픽: 매일, 서울, 한국경제)
allowed_media = ["매일경제", "서울경제", "한국경제"]

if st.button("분석 시작"):
    with st.spinner('네이버 증권 뉴스를 선별 중입니다...'):
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

                # 2. 뉴스 파트 (네이버 증권 뉴스 직접 수집)
                st.subheader(f"📰 {target_name} 네이버 증권 뉴스 (경제 3사)")
                
                # 네이버 증권 뉴스 검색 URL (종목 코드로 검색)
                news_url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(news_url, headers=headers)
                # 네이버 금융은 EUK-KR 인코딩을 쓰는 경우가 많아 한글 깨짐 방지 설정
                resp.encoding = 'euc-kr' 
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 뉴스 목록 추출
                titles = soup.select('td.title > a')
                infos = soup.select('td.info') # 언론사 정보

                count = 0
                for title_tag, info_tag in zip(titles, infos):
                    press = info_tag.text.strip()
                    # 지정된 3개 언론사만 필터링
                    if any(m in press for m in allowed_media):
                        title_text = title_tag.text.strip()
                        # 링크 주소 완성
                        link = "https://finance.naver.com" + title_tag['href']
                        
                        st.write(f"• [{press}] [{title_text}](%s)" % link)
                        count += 1
                        if count >= 10: break
                
                if count == 0:
                    st.info("최근 네이버 증권에 올라온 경제 3사 뉴스가 없습니다.")
                    st.write(f"[여기 눌러서 전체 뉴스 보기](https://finance.naver.com/item/news.naver?code={ticker})")
                    
        except Exception as e:
            st.error("데이터를 불러오는 중 오류가 발생했습니다.")
