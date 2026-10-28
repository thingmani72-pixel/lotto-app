import streamlit as st
import pandas as pd
import random
from collections import Counter

# 엑셀 파일 데이터 불러오기 (캐싱하여 속도 최적화)
@st.cache_data
def load_lotto_data():
    # 엑셀 파일 읽기
    df = pd.read_excel("lotto.xlsx")
    
    # 1. 역대 당첨 조합 리스트 만들기 (빠른 대조를 위해 Set 사용)
    winning_combinations = set(
        tuple(sorted([row['번호1'], row['번호2'], row['번호3'], row['번호4'], row['번호5'], row['번호6']]))
        for _, row in df.iterrows()
    )
    
    # 2. 모든 당첨 번호 추출하여 빈도 분석
    all_numbers = []
    for col in ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']:
        all_numbers.extend(df[col].tolist())
        
    freq = Counter(all_numbers)
    for i in range(1, 46):
        if i not in freq:
            freq[i] = 0
            
    return df, winning_combinations, freq

# 미당첨 조합 생성 함수
def generate_undrawn(winning_combinations, pool_numbers):
    attempts = 0
    while True:
        attempts += 1
        candidate = tuple(sorted(random.sample(pool_numbers, 6)))
        if candidate not in winning_combinations:
            return candidate, attempts

# --- Streamlit UI ---
st.set_page_config(page_title="엑셀 기반 로또 분석기", page_icon="📈")

st.title("📈 통계 기반 로또 미당첨 번호 추천기")
st.write("첨부된 `lotto.xlsx` 파일의 역대 당첨 기록을 분석하여 새로운 번호를 추출합니다.")

try:
    df, winning_combinations, freq = load_lotto_data()
    total_draws = len(df)
    st.info(f"성공적으로 데이터를 불러왔습니다. (총 {total_draws}회차 분석 완료)")
    
    # 통계 추출
    most_common = freq.most_common(6) # 가장 많이 나온 6개
    least_common = freq.most_common()[:-7:-1] # 가장 적게 나온 6개
    
    hot_numbers = [num for num, count in most_common]
    cold_numbers = [num for num, count in least_common]
    pool = list(set(hot_numbers + cold_numbers))
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🔥 역대 최다 출현 숫자 6개:\n{hot_numbers}")
    with col2:
        st.info(f"❄️ 역대 최소 출현 숫자 6개:\n{cold_numbers}")
        
    st.markdown("---")
    
    if st.button("🚀 위 숫자들을 조합하여 새 번호 뽑기", use_container_width=True):
        with st.spinner("미당첨 조합을 찾는 중..."):
            new_numbers, tries = generate_undrawn(winning_combinations, pool)
            
            st.success("역대 1등 번호와 겹치지 않는 새로운 조합입니다!")
            cols = st.columns(6)
            for i, num in enumerate(new_numbers):
                cols[i].markdown(
                    f"<div style='text-align:center; padding:20px; background-color:#f0f2f6; border-radius:50%; font-size:24px; font-weight:bold;'>{num}</div>", 
                    unsafe_allow_html=True
                )
            st.caption(f"내부 탐색 횟수: {tries}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")