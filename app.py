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

# 언론사 필터: 매일경제, 서울경제, 한국경제
allowed_media = ["매일경제", "서울경제", "한국경제"]

if st.button("분석 시작"):
    with st.spinner('데이터와 뉴스를 불러오는 중입니다...'):
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

                # 2. 뉴스 파트 (방식 변경: 더 안정적인 뉴스 검색)
                st.subheader(f"📰 {target_name} 최신 경제 뉴스")
                
                # 네이버 뉴스 검색 페이지를 통해 경제지 뉴스만 가져오기
                search_url = f"https://search.naver.com/search.naver?where=news&query={target_name}&sort=1"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(search_url, headers=headers)
                soup = BeautifulSoup(resp.text, 'html.parser')
                news_items = soup.select('ul.list_news > li')

                count = 0
                for item in news_items:
                    try:
                        press = item.select_one('a.info.press').text.replace('언론사 선정', '').strip()
                        # 지정된 언론사만 필터링
                        if any(m in press for m in allowed_media):
                            title_anchor = item.select_one('a.news_tit')
                            title = title_anchor.text
                            link = title_anchor['href']
                            
                            st.write(f"• [{press}] [{title}](%s)" % link)
                            count += 1
                            if count >= 10: break
                    except:
                        continue
                
                if count == 0:
                    st.info("선별된 주요 경제지 뉴스가 없습니다. (매일/서울/한국경제 기준)")
                    st.write(f"[여기 눌러서 직접 뉴스 보기](https://search.naver.com/search.naver?where=news&query={target_name})")
                    
        except Exception as e:
            st.error("분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
