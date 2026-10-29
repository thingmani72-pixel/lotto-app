import streamlit as st
import pandas as pd
import random
from collections import Counter

# 엑셀 파일 데이터 불러오기
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

# 💡 가중치(Weight) 기반 무작위 추출 함수 추가
def get_weighted_sample(pool, freq_dict, k):
    picked = set()
    while len(picked) < k:
        # 아직 뽑히지 않은 남은 번호들만 모아서 후보군 생성
        current_pool = [x for x in pool if x not in picked]
        # 후보군 번호들의 역대 당첨 횟수를 가중치(확률)로 설정
        weights = [freq_dict[x] for x in current_pool]
        
        # 가중치를 적용하여 1개씩 추출
        choice = random.choices(current_pool, weights=weights, k=1)[0]
        picked.add(choice)
    return picked

# 💡 황금 패턴 + 출현 비율 가중치 결합 알고리즘
def generate_weighted_smart_multiple(winning_combinations, freq_dict, num_games):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        
        # 1. 75% 확률로 1~9번에서 시작하는 패턴
        if random.random() < 0.75:
            single_count = random.choice([1, 2])
            pool_1_9 = list(range(1, 10))
            # 1~9번 안에서도 자주 나온 번호 위주로 추출
            combo = get_weighted_sample(pool_1_9, freq_dict, single_count)
            
            # 나머지 10~45번 구간에서도 자주 나온 번호 위주로 추출
            pool_10_45 = list(range(10, 46))
            combo.update(get_weighted_sample(pool_10_45, freq_dict, 6 - single_count))
            
        # 2. 25% 확률로 10~19번에서 시작하는 패턴
        else:
            pool_10_19 = list(range(10, 20))
            # 10~19번 안에서 시작 번호 1개를 가중치로 추출
            first_num = get_weighted_sample(pool_10_19, freq_dict, 1).pop()
            combo = {first_num}
            
            # 나머지 5개는 시작 번호보다 큰 숫자 중에서 가중치로 추출
            pool_rest = list(range(first_num + 1, 46))
            combo.update(get_weighted_sample(pool_rest, freq_dict, 5))
            
        candidate = tuple(sorted(combo))
        
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
st.title("🎯 가중치 + 패턴 기반 로또 생성기")
st.write("발견하신 **'시작 번호 황금 패턴'**을 지키면서, 과거에 **자주 당첨된 번호일수록 새 조합에 더 높은 확률로 포함**되도록 2중 설계되었습니다.")

try:
    df, winning_combinations, freq = load_lotto_data()
    total_draws = len(df)
    st.info(f"✅ 총 {total_draws}회차 데이터 분석 및 가중치(Weight) 엔진 가동 중")
    
    most_common = freq.most_common(6)
    least_common = freq.most_common()[:-7:-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🔥 역대 최다 출현 6개 (가중치 높음):\n{[num for num, _ in most_common]}")
    with col2:
        st.info(f"❄️ 역대 최소 출현 6개 (가중치 낮음):\n{[num for num, _ in least_common]}")
        
    st.markdown("---")
    
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button(f"🚀 {num_to_generate}게임 최적 조합으로 뽑기", use_container_width=True):
        with st.spinner("비율 가중치를 계산하며 미당첨 조합을 찾는 중..."):
            new_combinations, tries = generate_weighted_smart_multiple(winning_combinations, freq, num_to_generate)
            
            st.success("✨ 출현 비율과 패턴을 모두 만족하는 최적의 조합입니다!")
            
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
                
            st.caption(f"가중치 연산 및 필터링 횟수: 총 {tries}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")