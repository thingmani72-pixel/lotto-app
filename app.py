import streamlit as st
import sqlite3
import random
import requests
import time

# 1. DB 연결 상태를 유지하기 위한 캐싱 (Streamlit 재실행 시마다 연결 방지)
@st.cache_resource
def get_db_connection():
    # check_same_thread=False: 여러 스레드(Streamlit 렌더링)에서 동일 DB 접근 허용
    conn = sqlite3.connect("lotto_history.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winning_numbers (
            draw_no INTEGER PRIMARY KEY,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER
        )
    ''')
    conn.commit()
    return conn

# 2. 동행복권 API로 당첨 번호 수집 (프로그레스 바 UI 포함)
def update_db(conn, target_draws):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(draw_no) FROM winning_numbers")
    last_saved = cursor.fetchone()[0]
    
    start_draw = (last_saved + 1) if last_saved else 1
    
    if start_draw > target_draws:
        st.info("이미 최신 회차까지 데이터베이스가 업데이트되어 있습니다.")
        return 0

    st.write(f"{start_draw}회차부터 {target_draws}회차까지 수집을 시작합니다...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    saved_count = 0
    total_to_fetch = target_draws - start_draw + 1
    
    for i, draw_no in enumerate(range(start_draw, target_draws + 1)):
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        response = requests.get(url).json()
        
        if response.get("returnValue") == "success":
            nums = sorted([response[f"drwtNo{j}"] for j in range(1, 7)])
            cursor.execute('''
                INSERT OR IGNORE INTO winning_numbers (draw_no, n1, n2, n3, n4, n5, n6)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (draw_no, nums[0], nums[1], nums[2], nums[3], nums[4], nums[5]))
            saved_count += 1
            
        # UI 업데이트
        progress_bar.progress((i + 1) / total_to_fetch)
        status_text.text(f"진행 상황: {draw_no}회차 저장 중... ({(i+1)/total_to_fetch*100:.1f}%)")
        time.sleep(0.1) # API 차단 방지용 대기
        
    conn.commit()
    progress_bar.empty()
    status_text.empty()
    return saved_count

# 3. 미당첨 번호 생성 함수
def generate_undrawn_numbers(conn):
    cursor = conn.cursor()
    attempts = 0
    
    while True:
        attempts += 1
        candidate = tuple(sorted(random.sample(range(1, 46), 6)))
        
        cursor.execute('''
            SELECT draw_no FROM winning_numbers 
            WHERE n1=? AND n2=? AND n3=? AND n4=? AND n5=? AND n6=?
        ''', candidate)
        
        if not cursor.fetchone():
            return candidate, attempts

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="로또 미당첨 번호 추천기", page_icon="🍀")

st.title("🍀 로또 미당첨 조합 생성기")
st.write("역대 1등 당첨 기록과 대조하여, **단 한 번도 나온 적 없는 새로운 번호 조합**을 추출합니다.")

db_conn = get_db_connection()

# 사이드바: DB 관리
with st.sidebar:
    st.header("⚙️ 데이터베이스 관리")
    st.write("로또 API 서버에서 당첨 기록을 가져옵니다.")
    # 테스트를 위해 기본값을 100으로 설정 (실제로는 1240 등 최신 회차로 입력)
    target_draw_input = st.number_input("수집할 목표 회차", min_value=1, max_value=2000, value=100)
    
    if st.button("DB 업데이트 실행"):
        with st.spinner("데이터를 수집하는 중입니다..."):
            new_records = update_db(db_conn, target_draw_input)
            if new_records > 0:
                st.success(f"{new_records}개의 새로운 당첨 기록을 DB에 추가했습니다!")

# 메인 화면: 번호 생성
st.markdown("---")
st.subheader("새로운 운명의 번호 뽑기")

if st.button("🚀 번호 생성하기", use_container_width=True):
    # DB에 데이터가 하나라도 있는지 확인
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM winning_numbers")
    if cursor.fetchone()[0] == 0:
        st.warning("왼쪽 사이드바에서 먼저 'DB 업데이트 실행'을 눌러 과거 데이터를 가져와주세요.")
    else:
        with st.spinner("과거 기록과 대조하며 미당첨 번호를 찾는 중..."):
            new_lotto_numbers, tries = generate_undrawn_numbers(db_conn)
            
            st.success("새로운 미당첨 번호를 찾았습니다!")
            
            # 번호를 보기 좋게 시각화
            cols = st.columns(6)
            for i, num in enumerate(new_lotto_numbers):
                cols[i].markdown(
                    f"<div style='text-align:center; padding:20px; background-color:#f0f2f6; border-radius:50%; font-size:24px; font-weight:bold;'>{num}</div>", 
                    unsafe_allow_html=True
                )
            
            st.caption(f"이 번호를 찾기 위해 내부적으로 {tries}번의 난수 생성과 대조를 반복했습니다.")