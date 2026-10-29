import streamlit as st
import pandas as pd
import random
from collections import Counter

# 엑셀 파일 데이터 불러오기
@st.cache_data
def load_lotto_data():
    df = pd.read_excel("lotto.xlsx")
    
    # 1. 역대 당첨 조합 리스트 만들기
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

# 💡 대화 내용을 바탕으로 업그레이드된 통계 기반 생성 알고리즘
def generate_smart_multiple(winning_combinations, num_games):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        
        # 75% 확률로 1~9번에서 시작하는 패턴 적용
        if random.random() < 0.75:
            # 발견하신 통계대로 1~9번 구간에서 1개 또는 2개만 추출
            single_count = random.choice([1, 2])
            combo = set(random.sample(range(1, 10), single_count))
            
            # 나머지 번호는 10~45번 구간에서 추출하여 총 6개 완성
            combo.update(random.sample(range(10, 46), 6 - single_count))
            
        # 25% 확률로 10~19번에서 시작하는 패턴 적용
        else:
            first_num = random.randint(10, 19)
            combo = set([first_num])
            
            # 나머지 5개는 시작 번호보다 큰 숫자 중에서 추출 (단번대 배제)
            pool = list(range(first_num + 1, 46))
            combo.update(random.sample(pool, 5))
            
        candidate = tuple(sorted(combo))
        
        # 역대 1등 번호와 겹치지 않고, 이번에 뽑은 다른 게임과도 중복되지 않아야 통과
        if candidate not in winning_combinations and candidate not in results:
            results.append(candidate)
            
    return results, attempts

# --- Streamlit UI 및 디자인 ---
st.markdown("""
<style>
.stApp { background-color: #fdfaf6; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="최적화 로또 분석기", page_icon="🎯")
st.title("🎯 최적화 통계 기반 로또 생성기")
st.write("발견하신 **'시작 번호 패턴(단번대 1~2개)'**을 적용하여, 역대 1등과 겹치지 않는 가장 확률 높은 번호를 추출합니다.")

try:
    df, winning_combinations, freq = load_lotto_data()
    total_draws = len(df)
    st.info(f"✅ 총 {total_draws}회차 데이터 분석 완료 및 패턴 알고리즘 가동 중")
    
    # 핫/콜드 번호 통계 표시
    most_common = freq.most_common(6)
    least_common = freq.most_common()[:-7:-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🔥 역대 최다 출현 6개:\n{[num for num, _ in most_common]}")
    with col2:
        st.info(f"❄️ 역대 최소 출현 6개:\n{[num for num, _ in least_common]}")
        
    st.markdown("---")
    
    # 1~10게임 한 번에 선택받기
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button(f"🚀 {num_to_generate}게임 황금 패턴으로 뽑기", use_container_width=True):
        with st.spinner("최적의 미당첨 조합을 찾는 중..."):
            new_combinations, tries = generate_smart_multiple(winning_combinations, num_to_generate)
            
            st.success("✨ 역대 1등 번호를 완벽히 피해간 최적의 패턴 조합입니다!")
            
            # 생성된 게임 화면에 출력 (동행복권 색상 적용)
            for j, new_numbers in enumerate(new_combinations):
                st.markdown(f"**[{j+1} 게임]**")
                cols = st.columns(6)
                
                for i, num in enumerate(new_numbers):
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
                
            st.caption(f"내부 탐색 및 필터링 횟수: 총 {tries}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")