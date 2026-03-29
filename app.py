import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
from sklearn.ensemble import RandomForestClassifier
from GoogleNews import GoogleNews
import pandas as pd

# 앱 설정
st.set_page_config(page_title="민구의 AI 분석기", layout="wide")
st.title("📈 민구의 AI 주식 분석기")

target_name = st.text_input("분석할 종목명을 입력하세요", "삼성전자")

# 허용할 언론사 목록 (매일경제, 서울경제, 한국경제)
allowed_media = ["매일경제", "서울경제", "한국경제"]
# 필터링 단어 설정
bad_words = ["광고", "추천주", "무료체험", "카톡방", "상담", "급등주", "문의", "이벤트", "클릭"]
good_words = ["공급계약", "수주", "증자", "특허", "신사업", "최대실적", "M&A", "인수", "발표"]

if st.button("분석 시작"):
    with st.spinner('선택하신 언론사의 뉴스를 선별 중입니다...'):
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

                # 2. 뉴스 필터링 (언론사 고정)
                st.subheader(f"📰 {target_name} 핵심 뉴스 (매일/서울/한국경제)")
                gn = GoogleNews(lang='ko', period='7d')
                gn.search(target_name)
                news_results = gn.results()

                if news_results:
                    count = 0
                    for item in news_results:
                        title = item.get('title')
                        link = item.get('link')
                        media = item.get('media', '')

                        # 지정된 언론사가 아니면 통과
                        if not any(m in media for m in allowed_media):
                            continue
                        
                        # 광고성 단어 포함되면 통과
                        if any(word in title for word in bad_words):
                            continue
                        
                        # 중요 키워드 강조
                        is_important = any(word in title for word in good_words)
                        prefix = "🔥 [핵심] " if is_important else "• "
                        
                        # 화면에 출력 (링크 연결)
                        st.write(f"{prefix} [{media}] [{title}](%s)" % link)
                        count += 1
                        if count >= 10: break
                    
                    if count == 0:
                        st.write("선별된 주요 언론사 뉴스가 없습니다.")
                else:
                    st.write("최근 일주일간 뉴스가 없습니다.")
                    
        except Exception as e:
            st.write("분석 중 오류 발생")
