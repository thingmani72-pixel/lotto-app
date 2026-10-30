import streamlit as st
import pandas as pd
import random
from collections import Counter

# 엑셀 파일 데이터 불러오기 및 필터링 데이터 추출
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

# 💡 10중 극한 필터 통합 알고리즘
def generate_weighted_smart_multiple(winning_combinations, freq_dict, exclude_nums, cold_nums, num_games, 
                                     min_sum, max_sum, allowed_odd_counts, 
                                     use_consec, use_same_last, use_empty_sec, use_max_2_per_line):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        
        # 시작 패턴 강제
        if random.random() < 0.75:
            single_count = random.choice([1, 2])
            pool_1_9 = [x for x in range(1, 10) if x not in exclude_nums]
            single_count = min(single_count, len(pool_1_9)) 
            combo = get_weighted_sample(pool_1_9, freq_dict, cold_nums, single_count)
            pool_10_45 = [x for x in range(10, 46) if x not in exclude_nums]
            combo.update(get_weighted_sample(pool_10_45, freq_dict, cold_nums, 6 - len(combo)))
        else:
            pool_10_19 = [x for x in range(10, 20) if x not in exclude_nums]
            if not pool_10_19: continue
            first_num = get_weighted_sample(pool_10_19, freq_dict, cold_nums, 1).pop()
            combo = {first_num}
            pool_rest = [x for x in range(first_num + 1, 46) if x not in exclude_nums]
            combo.update(get_weighted_sample(pool_rest, freq_dict, cold_nums, 5))
            
        candidate = tuple(sorted(combo))
        
        if candidate not in winning_combinations and candidate not in results and len(candidate) == 6:
            # 1. 총합 & 홀짝 필터
            if not (min_sum <= sum(candidate) <= max_sum and sum(1 for x in candidate if x % 2 != 0) in allowed_odd_counts):
                continue
                
            # 💡 2. 고급 필터: 연속수 (예: 14, 15) 1쌍 이상 포함
            if use_consec:
                has_consec = any(candidate[i] + 1 == candidate[i+1] for i in range(5))
                if not has_consec: continue
                    
            # 💡 3. 고급 필터: 동일 끝수 (예: 12, 32) 1쌍 이상 포함
            if use_same_last:
                last_digits = [x % 10 for x in candidate]
                if len(set(last_digits)) == 6: continue # 6개 끝수가 모두 다르면 탈락
                
            # 💡 4. 고급 필터: 멸구간 (단번/10/20/30/40번대 중 최소 1개 구간 전멸)
            if use_empty_sec:
                sections = set()
                for x in candidate:
                    if x < 10: sections.add(0)
                    elif x < 20: sections.add(1)
                    elif x < 30: sections.add(2)
                    elif x < 40: sections.add(3)
                    else: sections.add(4)
                if len(sections) == 5: continue # 5개 구간에 숫자가 모두 있으면(멸구간이 없으면) 탈락
                
            # 💡 5. 고급 필터: 용지 가로줄당(7개 단위) 최대 2개까지만 마킹
            if use_max_2_per_line:
                # 1~7번=0줄, 8~14번=1줄 ... 43~45번=6줄
                line_counts = Counter((x - 1) // 7 for x in candidate)
                if max(line_counts.values()) > 2: continue # 한 줄에 3개 이상 쏠리면 탈락
                
            results.append(candidate)
            
    return results, attempts

# --- Streamlit UI 및 디자인 ---
st.markdown("""
<style>
.stApp { background-color: #fdfaf6; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="최적화 로또 분석기", page_icon="🎯", layout="wide")
st.title("🎯 10중 극한 필터 로또 생성기")

try:
    df, winning_combinations, freq, last_draw_numbers, last_draw_no, cold_numbers = load_lotto_data()
    
    col1, col2 = st.columns(2)
    with col1:
        st.warning(f"🚫 직전 **{last_draw_no}회차 번호 {sorted(list(last_draw_numbers))}** 완전 제외")
    with col2:
        st.success(f"🧊 **최근 10주 콜드 번호** {len(cold_numbers)}개 3배 우대 적용 중")
        
    st.markdown("---")
    st.markdown("### ⚙️ 1. 기본 통계 필터")
    
    col3, col4 = st.columns(2)
    with col3:
        sum_option = st.radio("총합 구간:", ("120 ~ 160 사이 (핵심 공략)", "100 ~ 170 사이 (안정적인 범위)", "제한 없음"))
        if sum_option.startswith("120"): min_s, max_s = 120, 160
        elif sum_option.startswith("100"): min_s, max_s = 100, 170
        else: min_s, max_s = 21, 255
            
    with col4:
        ratio_options = st.multiselect(
            "홀짝 비율 (복수 선택):",
            options=[3, 4, 2, 5, 1, 6, 0], default=[3, 4, 2],
            format_func=lambda x: f"홀{x} : 짝{6-x}"
        )
        if not ratio_options:
            st.error("최소 1개 이상의 홀짝 비율을 선택하세요.")
            st.stop()

    st.markdown("### 🧬 2. 4대 고급 패턴 필터")
    st.caption("실제 1등 당첨 번호의 약 60~70%가 가지는 패턴들입니다. (체크 시 활성화)")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5: use_consec = st.checkbox("연속수 1쌍 이상 포함", value=True, help="예: 14, 15처럼 이어진 번호 발생")
    with col6: use_same_last = st.checkbox("동일 끝수 1쌍 이상 포함", value=True, help="예: 12, 32처럼 끝자리가 같은 번호 발생")
    with col7: use_empty_sec = st.checkbox("멸구간 최소 1개 발생", value=True, help="단번/10/20/30/40번대 중 최소 1구간은 번호가 안 나옴")
    with col8: use_max_2_per_line = st.checkbox("용지 가로줄당 최대 2개", value=True, help="마킹 시 한 줄에 3개 이상 찍히는 쏠림 방지")
        
    st.markdown("---")
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button(f"🚀 {num_to_generate}게임 최적 조합으로 뽑기", use_container_width=True):
        with st.spinner("수만 번의 시뮬레이션을 거쳐 허수 조합을 폐기하는 중... (필터가 많을수록 약간의 시간이 소요될 수 있습니다)"):
            new_combinations, tries = generate_weighted_smart_multiple(
                winning_combinations, freq, last_draw_numbers, cold_numbers, 
                num_to_generate, min_s, max_s, ratio_options,
                use_consec, use_same_last, use_empty_sec, use_max_2_per_line
            )
            
            st.success(f"✨ 허수 조합 폐기 및 조건 탐색 횟수: 총 **{tries:,}번** 연산 완료!")
            
            for j, new_numbers in enumerate(new_combinations):
                total_sum = sum(new_numbers)
                odd_count = sum(1 for x in new_numbers if x % 2 != 0)
                
                st.markdown(f"**[{j+1} 게임]** (총합: {total_sum} / 홀짝: {odd_count}:{6-odd_count})")
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
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")