import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import pandas as pd
import feedparser

# 한글 금액 변환 함수
def format_korean_currency(amount_billion):
    if amount_billion >= 10000:
        jo = int(amount_billion // 10000)
        억 = int(amount_billion % 10000)
        return f"{jo}조 {억:,}억" if 억 > 0 else f"{jo}조"
    else:
        return f"{int(amount_billion):,}억"

# 앱 설정
st.set_page_config(page_title="민구의 데이터 분석기", layout="wide")
st.title("📊 민구의 주식 수급/데이터 분석기")

target_name = st.text_input("종목명을 입력하세요", "삼성전자")

if st.button("데이터 분석 시작"):
    with st.spinner('실시간 수급과 뉴스를 긁어오는 중...'):
        try:
            # 1. 종목 코드 찾기
            df_all = fdr.StockListing('KRX')
            ticker_row = df_all[df_all['Name'] == target_name]
            
            if ticker_row.empty:
                st.error(f"'{target_name}' 종목을 찾을 수 없습니다.")
            else:
                ticker = ticker_row['Code'].values[0]
                full_ticker = ticker + (".KS" if ticker.isdigit() else ".KQ")
                
                # 2. 데이터 가져오기 (가장 가벼운 1개월치만 사용)
                data = yf.download(full_ticker, period="1mo", progress=False).dropna()
                
                if not data.empty:
                    # [지표 계산]
                    last_price = float(data['Close'].iloc[-1])
                    last_volume = float(data['Volume'].iloc[-1])
                    trading_value_billion = (last_price * last_volume) / 100000000
                    korean_value = format_korean_currency(trading_value_billion)
                    
                    avg_vol_5d = data['Volume'].tail(5).mean()
                    vol_ratio = (last_volume / avg_vol_5d) * 100

                    # 상단 지표 출력
                    st.subheader(f"📈 {target_name} 실시간 수급 팩트")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("현재가", f"{int(last_price):,}원")
                    with col2:
                        st.metric("오늘 거래대금", korean_value)
                    with col3:
                        st.metric("5일 평균 대비 수급", f"{vol_ratio:.1f}%")

                    st.divider()

                    # 3. 실시간 뉴스 (RSS 방식 - 가장 안정적)
                    st.subheader(f"📰 {target_name} 일주일치 주요 뉴스")
                    rss_url = f"https://news.google.com/rss/search?q={target_name}+when:7d&hl=ko&gl=KR&ceid=KR:ko"
                    feed = feedparser.parse(rss_url)

                    if feed.entries:
                        for entry in feed.entries[:12]:
                            # 제목에서 언론사 분리
                            title = entry.title.rsplit(' - ', 1)[0]
                            link = entry.link
                            st.write(f"• [{title}](%s)" % link)
                    else:
                        st.info("최근 일주일간 뉴스가 없습니다.")
                else:
                    st.warning("주가 데이터를 가져올 수 없습니다.")

        except Exception as e:
            st.error("데이터 로드 중 일시적인 지연이 발생했습니다. 10초 뒤에 다시 눌러주세요.")
