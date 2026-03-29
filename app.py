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
# (앞부분 생략 - 이전과 동일)

# 5. 구글 뉴스 (디테일 강화 버전)
st.subheader(f"📰 {target_name} 관점 분석 뉴스")

# 내가 보기 싫은 단어들 (노이즈 제거)
bad_words = ["광고", "추천주", "무료체험", "카톡방", "종목상담", "급등주"]
# 내가 중요하게 보는 단어들 (하이라이트)
good_words = ["공급계약", "수주", "증자", "특허", "신사업", "최대실적"]

try:
    gn = GoogleNews(lang='ko', period='7d')
    gn.search(target_name)
    news_results = gn.results()

    if news_results:
        for item in news_results[:15]:
            title = item.get('title')
            
            # 1. 보기 싫은 뉴스 거르기
            if any(word in title for word in bad_words):
                continue
            
            # 2. 중요한 뉴스 강조하기
            display_title = title
            is_important = False
            for word in good_words:
                if word in title:
                    display_title = f"🔥 [핵심] {title}"
                    is_important = True
                    break
            
            # 3. 화면 출력
            if is_important:
                st.write(f"**{display_title}** ({item.get('media')})")
            else:
                st.write(f"- {title} ({item.get('media')})")
    else:
        st.write("최근 뉴스가 없습니다.")
except:
    st.write("뉴스 분석 중 오류 발생")
