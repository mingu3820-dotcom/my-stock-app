import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import feedparser
from datetime import datetime

# 앱 설정
st.set_page_config(page_title="민구의 AI 분석기", layout="wide")
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("분석할 종목명을 입력하세요", "삼성전자")

if st.button("분석 시작"):
    with st.spinner('AI 분석 및 최신 뉴스를 불러오는 중입니다...'):
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

                # 2. 뉴스 파트 (안정적인 구글 RSS 방식)
                st.subheader(f"📰 {target_name} 실시간 주요 뉴스")
                
                # 구글 뉴스 RSS 피드 주소 (한글, 한국 지역 설정)
                rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                feed = feedparser.parse(rss_url)

                if feed.entries:
                    for i, entry in enumerate(feed.entries[:20]): # 최대 20개
                        title = entry.title
                        link = entry.link
                        published = entry.published
                        # 언론사 분리 (보통 제목 끝에 - 언론사 형태로 붙음)
                        parts = title.rsplit(' - ', 1)
                        clean_title = parts[0]
                        media = parts[1] if len(parts) > 1 else "뉴스"
                        
                        st.write(f"• [{media}] [{clean_title}](%s) <span style='color:gray; font-size:12px;'>({published[:16]})</span>" % link, unsafe_allow_html=True)
                else:
                    st.info("최근 일주일간 검색된 뉴스가 없습니다.")
                    
        except Exception as e:
            st.error("분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")feedparser
