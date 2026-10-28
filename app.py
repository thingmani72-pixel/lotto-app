import streamlit as st
import pandas as pd
import random
from collections import Counter

@st.cache_data
def load_lotto_data():
    df = pd.read_excel("lotto.xlsx")
    
    winning_combinations = set(
        tuple(sorted([row['번호1'], row['번호2'], row['번호3'], row['번호4'], row['번호5'], row['번호6']]))
        for _, row in df.iterrows()
    )
    
    all_numbers = []
    for col in ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']:
        all_numbers.extend(df[col].tolist())
        
    freq = Counter(all_numbers)
    for i in range(1, 46):
        if i not in freq:
            freq[i] = 0
            
    return df, winning_combinations, freq

# 여러 게임을 중복 없이 한 번에 생성하는 함수
def generate_multiple_undrawn(winning_combinations, pool_numbers, num_games):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        candidate = tuple(sorted(random.sample(pool_numbers, 6)))
        
        # 과거 1등 번호가 아니면서, 방금 뽑은 다른 게임 번호와도 중복되지 않아야 함
        if candidate not in winning_combinations and candidate not in results:
            results.append(candidate)
            
    return results, attempts

# 앱 배경색 디자인 적용
st.markdown("""
<style>
.stApp {
    background-color: #fdfaf6; 
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="엑셀 기반 로또 분석기", page_icon="📈")
st.title("📈 통계 기반 로또 미당첨 번호 추천기")
st.write("첨부된 `lotto.xlsx` 파일의 역대 당첨 기록을 분석하여 새로운 번호를 추출합니다.")

try:
    df, winning_combinations, freq = load_lotto_data()
    total_draws = len(df)
    st.info(f"성공적으로 데이터를 불러왔습니다. (총 {total_draws}회차 분석 완료)")
    
    most_common = freq.most_common(6)
    least_common = freq.most_common()[:-7:-1]
    
    hot_numbers = [num for num, count in most_common]
    cold_numbers = [num for num, count in least_common]
    pool = list(set(hot_numbers + cold_numbers))
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🔥 역대 최다 출현 6개:\n{hot_numbers}")
    with col2:
        st.info(f"❄️ 역대 최소 출현 6개:\n{cold_numbers}")
        
    st.markdown("---")
    
    # 1~10게임 선택 버튼 추가 (기본값 5게임)
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button("🚀 위 숫자들을 조합하여 새 번호 뽑기", use_container_width=True):
        with st.spinner(f"{num_to_generate}게임의 미당첨 조합을 찾는 중..."):
            new_combinations, tries = generate_multiple_undrawn(winning_combinations, pool, num_to_generate)
            
            st.success(f"역대 1등 번호와 겹치지 않는 {num_to_generate}개의 새로운 조합입니다!")
            
            # 선택한 게임 수만큼 반복하여 화면에 출력
            for j, new_numbers in enumerate(new_combinations):
                st.markdown(f"**[{j+1} 게임]**")
                cols = st.columns(6)
                
                for i, num in enumerate(new_numbers):
                    # 로또 공 색상 로직
                    if num <= 10: bg_color, text_color = "#fbc400", "#000000"
                    elif num <= 20: bg_color, text_color = "#69c8f2", "#000000"
                    elif num <= 30: bg_color, text_color = "#ff7272", "#ffffff"
                    elif num <= 40: bg_color, text_color = "#aaaaaa", "#ffffff"
                    else: bg_color, text_color = "#b0d840", "#000000"

                    cols[i].markdown(
                        f"<div style='text-align:center; padding:15px; margin-bottom:10px; background-color:{bg_color}; color:{text_color}; border-radius:50%; font-size:20px; font-weight:bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>{num}</div>", 
                        unsafe_allow_html=True
                    )
                st.markdown("---")
                
            st.caption(f"내부 탐색 횟수: 총 {tries}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")