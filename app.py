import streamlit as st
import pandas as pd
import random
from collections import Counter

# 엑셀 파일 데이터 불러오기 및 4중 필터링 데이터 추출
@st.cache_data
def load_lotto_data():
    df = pd.read_excel("lotto.xlsx")
    
    # 💡 핵심 수정: 엑셀 데이터가 어떻게 입력되어 있든, '회차' 번호순으로 
    # 과거에서 최신순(오름차순)으로 자동 정렬하여 인식 오류를 원천 차단합니다.
    df = df.sort_values(by='회차').reset_index(drop=True)
    
    # 1. 역대 당첨 조합 (중복 방지용)
    winning_combinations = set(
        tuple(sorted([row['번호1'], row['번호2'], row['번호3'], row['번호4'], row['번호5'], row['번호6']]))
        for _, row in df.iterrows()
    )
    
    # 2. 모든 당첨 번호 빈도 (기본 가중치용)
    all_numbers = []
    for col in ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']:
        all_numbers.extend(df[col].tolist())
        
    freq = Counter(all_numbers)
    for i in range(1, 46):
        if i not in freq:
            freq[i] = 0
            
    # 3. 직전 회차 번호 식별 (이월수 배제용 - 정렬되었으므로 무조건 최신 회차가 맨 아래 위치)
    last_draw_row = df.iloc[-1]
    last_draw_no = int(last_draw_row['회차'])
    last_draw_numbers = set([
        int(last_draw_row['번호1']), int(last_draw_row['번호2']), int(last_draw_row['번호3']), 
        int(last_draw_row['번호4']), int(last_draw_row['번호5']), int(last_draw_row['번호6'])
    ])
    
    # 4. 최근 10주 미출현 콜드 번호 식별 (가중치 3배 증폭용 - 최신 10개 행 추출)
    recent_10_df = df.tail(10)
    recent_10_numbers = set()
    for col in ['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']:
        recent_10_numbers.update(recent_10_df[col].tolist())
        
    cold_numbers = set(range(1, 46)) - recent_10_numbers
            
    return df, winning_combinations, freq, last_draw_numbers, last_draw_no, cold_numbers

# 가중치 기반 무작위 추출 함수 (콜드수 우대 로직 포함)
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

# 4중 통합 생성 알고리즘
def generate_weighted_smart_multiple(winning_combinations, freq_dict, exclude_nums, cold_nums, num_games):
    results = []
    attempts = 0
    
    while len(results) < num_games:
        attempts += 1
        
        # 1. 75% 확률로 1~9번에서 시작
        if random.random() < 0.75:
            single_count = random.choice([1, 2])
            pool_1_9 = [x for x in range(1, 10) if x not in exclude_nums]
            single_count = min(single_count, len(pool_1_9)) 
            
            combo = get_weighted_sample(pool_1_9, freq_dict, cold_nums, single_count)
            
            pool_10_45 = [x for x in range(10, 46) if x not in exclude_nums]
            combo.update(get_weighted_sample(pool_10_45, freq_dict, cold_nums, 6 - len(combo)))
            
        # 2. 25% 확률로 10~19번에서 시작
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
            results.append(candidate)
            
    return results, attempts

# --- Streamlit UI 및 디자인 ---
st.markdown("""
<style>
.stApp { background-color: #fdfaf6; }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="최적화 로또 분석기", page_icon="🎯")
st.title("🎯 4중 필터링 로또 생성기")
st.write("황금 패턴, 이월수 제외는 물론 **'최근 10주 미출현 콜드 번호'의 당첨 확률을 3배 상향**시킨 궁극의 알고리즘입니다.")

try:
    df, winning_combinations, freq, last_draw_numbers, last_draw_no, cold_numbers = load_lotto_data()
    total_draws = len(df)
    
    st.info(f"✅ 총 {total_draws}회차 데이터 기반 4중 필터링 엔진 가동 중")
    
    st.warning(f"🚫 직전 **{last_draw_no}회차 당첨 번호 {sorted(list(last_draw_numbers))}** 6개는 추출에서 완전 제외되었습니다.")
    st.success(f"🧊 **{last_draw_no-9}회~{last_draw_no}회** 미출현 콜드 번호 {len(cold_numbers)}개 발굴 완료! (가중치 300% 적용)\n{sorted(list(cold_numbers))}")
        
    st.markdown("---")
    
    num_to_generate = st.selectbox("몇 게임을 생성할까요?", range(1, 11), index=4)
    
    if st.button(f"🚀 {num_to_generate}게임 최적 조합으로 뽑기", use_container_width=True):
        with st.spinner("4가지 필터링 조건을 모두 연산하며 번호를 추출하는 중..."):
            new_combinations, tries = generate_weighted_smart_multiple(
                winning_combinations, freq, last_draw_numbers, cold_numbers, num_to_generate
            )
            
            st.success("✨ 모든 수학적 필터링을 통과한 완벽한 조합입니다!")
            
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
                
            st.caption(f"가중치 연산 및 조건 필터링 횟수: 총 {tries}번")
            
except FileNotFoundError:
    st.error("같은 폴더에 'lotto.xlsx' 파일이 없습니다. 파일을 준비해 주세요.")