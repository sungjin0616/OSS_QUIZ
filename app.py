import time
import re
import importlib
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import quiz_data as quiz_module

st.set_page_config(page_title="광운대의 장소 맞추기!!!!", page_icon="🏫", layout="centered")

STUDENT_ID = "2025404041" 
STUDENT_NAME = "강성진"

BASE_DIR = Path(__file__).parent
_QUIZ_DATA_PATH = BASE_DIR / "quiz_data.py"

@st.cache_data
def load_quiz_data(quiz_data_mtime: float):
    importlib.reload(quiz_module)
    return quiz_module.quiz_data

def validate_username(username: str) -> list[str]:
    u = (username or "").strip()
    errors: list[str] = []
    if not u:
        return ["아이디를 입력해주세요."]
    if len(u) < 6 or len(u) > 16:
        errors.append("아이디 길이는 6~16자여야 합니다.")
    if not re.fullmatch(r"[A-Za-z0-9]+", u):
        errors.append("아이디는 오직 영문과 숫자로만 이루어져야 합니다.")
    return errors

def validate_password(password: str) -> list[str]:
    p = password or ""
    errors: list[str] = []
    if not p:
        return ["비밀번호를 입력해주세요."]
    if len(p) < 8 or len(p) > 32:
        errors.append("비밀번호 길이는 8~32자여야 합니다.")
    if len(re.findall(r"[A-Za-z]", p)) < 4:
        errors.append("비밀번호는 영문을 4자 이상 포함해야 합니다.")
    if len(re.findall(r"\d", p)) < 4:
        errors.append("비밀번호는 숫자를 4자 이상 포함해야 합니다.")
    if len(re.findall(r"[^A-Za-z0-9]", p)) < 1:
        errors.append("비밀번호는 특수문자를 1개 이상 포함해야 합니다.")
    return errors

def check_login(username: str, password: str) -> bool:
    return (len(validate_username(username)) == 0) and (len(validate_password(password)) == 0)

def _norm_text(s: str) -> str:
    return "".join((s or "").strip().lower().split())

def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "current_index": 0,
        "score": 0,
        "quiz_finished": False,
        "results": [],
        "question_start_time": None,
        "hints_used": {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_quiz():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.quiz_finished = False
    st.session_state.results = []
    st.session_state.question_start_time = None
    st.session_state.hints_used = {}

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    reset_quiz()

init_session()
questions = load_quiz_data(_QUIZ_DATA_PATH.stat().st_mtime)

st.title("🏫 광운대의 장소 맞추기!!!!")
st.caption("건물, 장소 사진을 보고 정답을 맞춰보세요! 힌트없이 맞추면 10점, 힌트를 사용하고 맞추면 5점입니다!")
st.write(f"**제출자:** 정보융합학부 {STUDENT_ID} {STUDENT_NAME}")
st.divider()

if not st.session_state.logged_in:
    st.subheader("로그인")
    st.info(
        "💡 **로그인 규칙**\n"
        "- **아이디:** 영문/숫자만 사용, 6~16자\n"
        "- **비밀번호:** 8~32자, 영문 4자 이상, 숫자 4자 이상, 특수문자 1개 이상 포함 필수"
    )

    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")

    if submitted:
        u_errors = validate_username(username)
        p_errors = validate_password(password)

        if u_errors or p_errors:
            if u_errors:
                st.error("아이디 조건 오류:\n- " + "\n- ".join(u_errors))
            if p_errors:
                st.error("비밀번호 조건 오류:\n- " + "\n- ".join(p_errors))
        elif check_login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            reset_quiz()
            st.rerun()
        else:
            st.error("로그인에 실패했습니다.")

else:
    st.sidebar.write(f"👤 접속 중: **{st.session_state.username}**님")
    if st.sidebar.button("로그아웃"):
        logout()
        st.rerun()

    if st.session_state.quiz_finished:
        total = st.session_state.score
        total_questions = len(questions)
        correct_count = sum(1 for r in st.session_state.results if r.get("is_correct"))
        total_elapsed = sum(float(r.get("elapsed", 0.0)) for r in st.session_state.results)

        st.header("🎊 퀴즈 종료!")
        st.success(f"당신의 최종 점수: {total} / {total_questions * 10}점")
        st.info(f"⏱️ 12문제를 푸는 데 총 **{total_elapsed:.2f}초**가 걸렸습니다.")
        
        st.divider()
        st.subheader("🧐 문항별 상세 리뷰")

        for idx, res in enumerate(st.session_state.results, start=1):
            icon = "✅ 정답!" if res["is_correct"] else "❌ 오답"
            with st.expander(f"문제 {idx}: {res['question']} - {icon}"):
                st.write(f"**내가 쓴 답:** {res['selected_option']}")
                st.write(f"**정답:** {res['correct_option']}")
                st.write(f"**소요 시간:** {res['elapsed']:.2f}초")
                st.write(f"**획득 점수:** {res.get('earned_score', 0)}점")
                st.warning(f"📍 **장소 정보:** {res['description']}")

        st.divider()
        if st.button("다시 풀기"):
            reset_quiz()
            st.rerun()

    else:
        total_questions = len(questions)
        current_index = st.session_state.current_index
        current_question = questions[current_index]

        st.subheader(f"📝 퀴즈 진행 중 ({current_index + 1} / {total_questions})")
        st.progress((current_index + 1) / total_questions)

        if st.session_state.question_start_time is None:
            st.session_state.question_start_time = time.time()

        image_path = BASE_DIR / "images" / current_question["image"]
        try:
            st.image(str(image_path), use_container_width=True)
        except Exception:
            st.error(f"이미지를 찾을 수 없습니다: {image_path}\nimages 폴더에 사진을 넣어주세요.")

        st.markdown(f"### Q. {current_question['question']}")

        hint = current_question.get("hint")
        hint_key = f"hint_{current_question['id']}"
        
        if hint:
            if st.button("💡 힌트 보기"):
                st.session_state.hints_used[hint_key] = True
                
            if st.session_state.hints_used.get(hint_key):
                st.info(f"힌트: {hint}")

        with st.form(f"answer_form_{current_question['id']}", clear_on_submit=False):
            user_text = st.text_input("정답을 입력하세요.")
            
            components.html(
                """
                <script>
                (() => {
                  const focusCurrentFormTextInput = () => {
                    try {
                      const forms = Array.from(parent.document.querySelectorAll('form'));
                      const form = forms[forms.length - 1];
                      if (!form) return false;
                      const target = form.querySelector('input[type="text"]');
                      if (target) {
                        target.focus();
                        target.select?.();
                        return true;
                      }
                    } catch (e) {}
                    return false;
                  };
                  let tries = 0;
                  const tick = () => {
                    tries += 1;
                    if (focusCurrentFormTextInput()) return;
                    if (tries < 20) setTimeout(tick, 80);
                  };
                  setTimeout(tick, 30);
                })();
                </script>
                """,
                height=0,
            )

            submitted = st.form_submit_button("제출")

        if submitted:
            elapsed = time.time() - st.session_state.question_start_time
            norm_choice = _norm_text(user_text)
            accepted = {_norm_text(a) for a in current_question.get("answers", [])}
            
            is_correct = norm_choice in accepted

            hint_key = f"hint_{current_question['id']}"
            used_hint = st.session_state.hints_used.get(hint_key, False)
            
            if is_correct:
                earned_score = 5 if used_hint else 10 
            else:
                earned_score = 0 
            st.session_state.score += earned_score
            
            correct_option = ", ".join(current_question["answers"])

            st.session_state.results.append({
                "question": current_question["question"],
                "selected_option": user_text,
                "correct_option": correct_option,
                "elapsed": elapsed,
                "is_correct": is_correct,
                "description": current_question["description"],
                "earned_score": earned_score
            })

            st.session_state.current_index += 1
            st.session_state.question_start_time = None

            if st.session_state.current_index >= total_questions:
                st.session_state.quiz_finished = True

            st.rerun()