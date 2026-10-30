import streamlit as st
import pandas as pd
import random
from collections import Counter

@st.cache_data
def load_lotto_data():
    df = pd.read_excel("lotto.xlsx")
    df = df.sort_values(by='회차').reset_index(drop=True)
    
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
            
    last_draw_row = df.iloc[-1]
    last_draw_no = int(last_draw_row['회차'])
    last_draw_numbers = set([
        int(last_draw_row['번호1']), int(last_draw_row['번호2']), int(last_draw_row['번호3']), 
        int(last_draw_row['번호4']), int(last_draw_row['번호5']), int(last_draw_row['번호6'])
    ])
    
    recent_10_df = df.tail(10)
    recent_10_numbers = set()
    for col in ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']:
        recent_10_numbers.update(recent_10_df[col].tolist())
        
    cold_numbers = set(range(1, 46)) - recent_10_numbers
            
    return df, winning_combinations, freq, last_draw_numbers, last_draw_no, cold_numbers

def get_weighted_sample(pool, freq_dict, cold_nums, k):
    picked = set()
    while len(picked) < k:
        current_pool = [x for x in pool if x not in picked]
        if not current_pool:
            break
            
        weights = []
        for x in current_pool:
            w = freq_dict[x]
            if x in cold_nums:
                w *= 3.0 
            weights.append(w)
            
        choice = random.choices(current_pool, weights=weights, k=1)[0]
        picked.add(choice)
    return picked

# 💡 선택된 UI 옵션(min_sum, max_sum, allowed_odd_counts)을 매개변수로 받도록 수정
def generate_weighted_smart_multiple(winning_combinations, freq_dict, exclude_nums, cold_nums, num_games, min_sum, max_sum, allowed_odd_counts):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        
        if random.random() < 0.75:
            single_count = random.choice([1, 2])
            pool_1_9 = [x for x in range(1, 10) if x not in exclude_nums]
            single_count = min(single_count, len(pool_1_9)) 
            
            combo = get_weighted_sample(pool_1_9, freq_dict, cold_nums, single_count)
            
            pool_10_45 = [x for x in range(10, 46) if x not in exclude_nums]
            combo.update(get_weighted_sample(pool_10_45, freq_dict, cold_nums, 6 - len(combo)))
            
        else:
            pool_10_19 = [x for x in range(10, 20) if x not in exclude_nums]
            if not pool_10_19: 
                continue
            first_num = get_weighted_sample(pool_10_19, freq_dict, cold_nums, 1).pop()
            combo = {first_num}
            
            pool_rest = [x for x in range(first_num + 1, 46) if x not in exclude_nums]
            combo.update(get_weighted_sample(pool_rest, freq_dict, cold_nums, 5))
            
        candidate = tuple(sorted(combo))
        
        if candidate not in winning_combinations and candidate not in results and len(candidate) == 6:
            total_sum = sum(candidate)
            odd_count = sum(1 for x in candidate if x % 2 != 0)
            
            # 💡 UI에서 선택한 조건에 부합하는지 검사
            if min_sum <= total_sum <= max_sum and odd_count in allowed_odd_counts:
                results.append(candidate)
            
    return results, attempts

# --- Streamlit UI 및 디자인 ---
st.markdown("""
<style>
.stApp { background-color: #fdfaf6; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="최적화 로또 분석기", page_icon="🎯")
st.title("🎯 맞춤형 6중 필터 로또 생성기")

try:
    df, winning_combinations, freq, last_draw_numbers, last_draw_no, cold_numbers = load_lotto_data()
    
    st.warning(f"🚫 직전 **{last_draw_no}회차 번호 {sorted(list(last_draw_numbers))}** 완전 제외")
    st.success(f"🧊 **최근 10주 콜드 번호** {len(cold_numbers)}개 3배 우대 적용 중\n{sorted(list(cold_numbers))}")
        
    st.markdown("### ⚙️ 생성 옵션 설정")
    
    # 💡 1. 총합 구간 선택 (Radio 버튼)
    sum_option = st.radio(
        "총합 필터 구간:",
        ("120 ~ 160 사이 (핵심 공략)", "100 ~ 170 사이 (안정적인 범위)", "제한 없음")
    )
    
    if sum_option.startswith("120"):
        min_s, max_s = 120, 160
    elif sum_option.startswith("100"):
        min_s, max_s = 100, 170
    else:
        min_s, max_s = 21, 255 # 사실상 제한 없음
        
    # 💡 2. 홀짝 비율 선택 (Multi-select)
    ratio_options = st.multiselect(
        "홀짝 비율 (복수 선택 가능):",
        options=[3, 4, 2, 5, 1, 6, 0],
        default=[3, 4, 2], # 통계상 확률 높은 3:3, 4:2, 2:4를 기본 선택값으로 설정
        format_func=lambda x: f"홀{x} : 짝{6-x}"
    )
    
    # 예외 처리: 홀짝 비율을 아무것도 선택하지 않았을 때 방어 코드
    if not ratio_options:
        st.error("최소 1개 이상의 홀짝 비율을 선택해야 합니다.")
        st.stop()
        
    st.markdown("---")
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button(f"🚀 {num_to_generate}게임 최적 조합으로 뽑기", use_container_width=True):
        with st.spinner("선택하신 맞춤형 필터링 조건을 연산 중입니다..."):
            new_combinations, tries = generate_weighted_smart_multiple(
                winning_combinations, freq, last_draw_numbers, cold_numbers, 
                num_to_generate, min_s, max_s, ratio_options
            )
            
            st.success("✨ 맞춤형 수학적 필터링을 통과한 조합입니다!")
            
            for j, new_numbers in enumerate(new_combinations):
                total_sum = sum(new_numbers)
                odd_count = sum(1 for x in new_numbers if x % 2 != 0)
                even_count = 6 - odd_count
                
                st.markdown(f"**[{j+1} 게임]** (총합: {total_sum} / 홀짝: {odd_count}:{even_count})")
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
                
            st.caption(f"허수 조합 폐기 및 조건 탐색 횟수: 총 {tries:,}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")