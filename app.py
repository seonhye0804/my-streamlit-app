import json
import re
import streamlit as st
from typing import List, Dict, Any

# OpenAI (최신 SDK 기준)
from openai import OpenAI


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(page_title="이제뭐하지", layout="wide")

APP_TITLE = "이제뭐하지"


# =========================================================
# 세션 상태 초기화
# =========================================================
def init_session():
    if "page" not in st.session_state:
        st.session_state.page = 1

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}

    if "job_reco" not in st.session_state:
        st.session_state.job_reco = []

    if "filter_questions" not in st.session_state:
        st.session_state.filter_questions = []

    if "filter_answers" not in st.session_state:
        st.session_state.filter_answers = {}

    if "final_jobs" not in st.session_state:
        st.session_state.final_jobs = []

    if "selected_job" not in st.session_state:
        st.session_state.selected_job = None

    if "roadmap" not in st.session_state:
        st.session_state.roadmap = None


init_session()


# =========================================================
# 유틸: 페이지 이동
# =========================================================
def go(page_num: int):
    st.session_state.page = page_num


# =========================================================
# OpenAI 유틸
# =========================================================
def get_client() -> OpenAI:
    return OpenAI(api_key=st.session_state.api_key)


def safe_json_extract(text: str) -> dict:
    """
    모델이 JSON만 반환하라고 해도 가끔 설명이 섞임.
    JSON 블록만 추출해서 파싱하려는 안전장치.
    """
    text = text.strip()

    # 1) 완전 JSON이면 바로 파싱
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) ```json ... ``` 형태 추출
    codeblock = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if codeblock:
        try:
            return json.loads(codeblock.group(1))
        except Exception:
            pass

    # 3) 첫 { ~ 마지막 } 추출
    brace = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(1))
        except Exception:
            pass

    return {}


def openai_chat_json(system: str, user: str, model: str = "gpt-4o-mini") -> dict:
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.6,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = resp.choices[0].message.content
    return safe_json_extract(content)


# =========================================================
# 2페이지 질문 리스트 (요구사항 반영)
# =========================================================
def render_user_questions_form() -> Dict[str, Any]:
    """
    요구된 질문 리스트 그대로 UI로 구성.
    반환: user_answers dict
    """
    answers = st.session_state.user_answers

    st.subheader("돈은 얼마나 벌고 싶나요?")
    answers["money"] = st.radio(
        "money",
        ["상관없음", "평균 정도면 만족", "많이 벌고 싶음", "최대한 많이 벌고 싶음"],
        index=0 if "money" not in answers else ["상관없음", "평균 정도면 만족", "많이 벌고 싶음", "최대한 많이 벌고 싶음"].index(answers["money"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("어디에서 일하고 싶나요?")
    answers["location"] = st.radio(
        "location",
        ["서울", "수도권", "지방 광역시", "세종", "농어촌"],
        index=0 if "location" not in answers else ["서울", "수도권", "지방 광역시", "세종", "농어촌"].index(answers["location"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("직업의 형태는 무엇이 좋나요?")
    answers["job_type"] = st.radio(
        "job_type",
        ["직장인", "프리랜서", "전문직"],
        index=0 if "job_type" not in answers else ["직장인", "프리랜서", "전문직"].index(answers["job_type"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("통근시간은 최대 얼마 이하였으면 좋겠나요?")
    answers["commute"] = st.radio(
        "commute",
        ["30분", "1시간", "1시간 반", "2시간", "2시간 반"],
        index=1 if "commute" not in answers else ["30분", "1시간", "1시간 반", "2시간", "2시간 반"].index(answers["commute"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("조직 문화는 어땠으면 좋겠나요?")
    answers["culture"] = st.radio(
        "culture",
        [
            "명확하지 않은 지시사항+창의적 분위기",
            "상명하복의 권위적 분위기",
            "처음엔 텃세가 있을 수 있으나 친해지면 단단한 결속",
            "개인주의의 차가운 분위기",
            "회식, 술자리 등 뭐든지 함께 분위기",
        ],
        index=0 if "culture" not in answers else [
            "명확하지 않은 지시사항+창의적 분위기",
            "상명하복의 권위적 분위기",
            "처음엔 텃세가 있을 수 있으나 친해지면 단단한 결속",
            "개인주의의 차가운 분위기",
            "회식, 술자리 등 뭐든지 함께 분위기",
        ].index(answers["culture"]),
        label_visibility="collapsed",
    )

    st.subheader("조직 성비는 어땠으면 좋겠나요?")
    answers["gender_ratio"] = st.radio(
        "gender_ratio",
        ["남 다수", "여 다수", "반반", "상관없음"],
        index=3 if "gender_ratio" not in answers else ["남 다수", "여 다수", "반반", "상관없음"].index(answers["gender_ratio"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.subheader("건강상 약점이 있나요?")
    answers["health"] = st.multiselect(
        "health",
        ["없음", "눈의 피로", "허리, 목", "호흡기", "근육 및 운동능력", "두통", "스트레스 취약"],
        default=answers.get("health", ["없음"]),
        label_visibility="collapsed",
    )

    st.subheader("무조건 지켜져야 하는 것은?")
    answers["must_have"] = st.radio(
        "must_have",
        [
            "따박따박 나오는 월급",
            "세상의 인정",
            "몸 상하지 않는 것",
            "칼퇴 등 개인 시간 확보",
            "일의 재미 및 자아실현",
            "안정된 고용",
        ],
        index=0 if "must_have" not in answers else [
            "따박따박 나오는 월급",
            "세상의 인정",
            "몸 상하지 않는 것",
            "칼퇴 등 개인 시간 확보",
            "일의 재미 및 자아실현",
            "안정된 고용",
        ].index(answers["must_have"]),
        label_visibility="collapsed",
    )

    st.subheader("내가 절대 못하겠는 것은? (복수응답)")
    answers["cant_do"] = st.multiselect(
        "cant_do",
        ["음악", "미술", "체육", "국어", "외국어", "일반사회", "수학", "과학", "공학"],
        default=answers.get("cant_do", []),
        label_visibility="collapsed",
    )

    st.subheader("내가 잘하는 것에 결합될 수 있는 행동 중 끌리는 것은?")
    answers["preferred_action"] = st.radio(
        "preferred_action",
        ["~를 가르치기", "~를 고치기", "~를 지적하기", "~를 연구하기"],
        index=0 if "preferred_action" not in answers else ["~를 가르치기", "~를 고치기", "~를 지적하기", "~를 연구하기"].index(answers["preferred_action"]),
        horizontal=True,
        label_visibility="collapsed",
    )

    # 추가(현실적 추천을 위해)
    st.markdown("---")
    st.subheader("추가 정보 (추천 정확도를 위해)")
    answers["education"] = st.radio(
        "학력",
        ["고졸 이하", "대학 재학", "대학 졸업", "대학원 재학/졸업"],
        index=1 if "education" not in answers else ["고졸 이하", "대학 재학", "대학 졸업", "대학원 재학/졸업"].index(answers["education"]),
        horizontal=True,
        label_visibility="collapsed",
    )
    answers["major"] = st.text_input(
        "전공(예: 국어국문학 / 경영학 / 시각디자인 / 컴퓨터공학 등)",
        value=answers.get("major", ""),
        placeholder="전공을 입력하세요",
    )

    st.session_state.user_answers = answers
    return answers


# =========================================================
# 2 -> 3: OpenAI로 추천 직무 리스트 생성
# =========================================================
def generate_job_recommendations(user_answers: Dict[str, Any]) -> List[Dict[str, Any]]:
    system = """
너는 취업/진로 상담 AI다.
사용자의 성향/조건을 보고 '초기 취준생'에게 현실적인 추천 직무 리스트를 만든다.

반드시 아래 JSON 형식으로만 출력하라.
"""

    user = f"""
사용자 입력 정보는 다음과 같다:
{json.dumps(user_answers, ensure_ascii=False, indent=2)}

요구사항:
- 추천 직무 10~15개
- 각 직무는 한국 기준으로 현실적인 직무여야 함
- 직무는 너무 거창하지 않게 (예: "CEO" 같은 것 금지)
- 직무별로 다음 정보를 포함:
  - job_title: 직무명
  - category: (예: 마케팅/기획/교육/디자인/개발/공공/전문직/콘텐츠 등)
  - why_fit: 왜 이 사용자에게 맞는지 1~2문장
  - requirements_hint: 해당 직무에 일반적으로 필요한 조건(학력/자격/전공 등)을 짧게

출력 JSON 스키마:
{{
  "jobs": [
    {{
      "job_title": "...",
      "category": "...",
      "why_fit": "...",
      "requirements_hint": "..."
    }}
  ]
}}
"""

    data = openai_chat_json(system=system, user=user)
    jobs = data.get("jobs", [])

    # 최소 안전장치
    cleaned = []
    for j in jobs:
        if isinstance(j, dict) and j.get("job_title"):
            cleaned.append(j)

    return cleaned


# =========================================================
# 3페이지: 필터링 질문 생성 (OpenAI)
# =========================================================
def generate_filter_questions(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    system = """
너는 진로추천 앱의 '필터링 질문 생성기'다.

입력으로 추천 직무 리스트가 주어진다.
여기서 일부 직무는 특정 조건이 반드시 필요하다(예: 의사, 변호사, 약사, 교사 등).

너의 목표는:
- 사용자가 '해당 직무가 현실적으로 가능한지' 판단하기 위한 질문을 자동 생성하는 것.

반드시 JSON 형식으로만 출력하라.
"""

    user = f"""
추천 직무 리스트:
{json.dumps(jobs, ensure_ascii=False, indent=2)}

요구사항:
- 질문은 3~7개 정도 (너무 많으면 안 됨)
- 질문은 직무 리스트에 기반해서만 생성
- 질문마다 아래 정보를 포함:
  - id: 짧은 식별자(영문)
  - question: 질문 문장
  - type: "yesno" 또는 "choice"
  - options: type이 choice면 선택지 리스트, yesno면 ["예","아니오"]
  - affects_jobs: 이 질문이 영향을 주는 직무명 리스트

예시:
의사가 있으면 -> "의대 졸업(또는 재학) 여부" 같은 질문 생성

출력 JSON 스키마:
{{
  "questions": [
    {{
      "id": "medical_school",
      "question": "의대 졸업(또는 재학) 여부가 있나요?",
      "type": "yesno",
      "options": ["예","아니오"],
      "affects_jobs": ["의사"]
    }}
  ]
}}
"""

    data = openai_chat_json(system=system, user=user)
    qs = data.get("questions", [])

    cleaned = []
    for q in qs:
        if isinstance(q, dict) and q.get("id") and q.get("question"):
            if q.get("type") not in ["yesno", "choice"]:
                continue
            if "options" not in q or not isinstance(q["options"], list):
                continue
            if "affects_jobs" not in q or not isinstance(q["affects_jobs"], list):
                continue
            cleaned.append(q)

    return cleaned


# =========================================================
# 3페이지: 필터링 적용
# =========================================================
def apply_filtering(
    jobs: List[Dict[str, Any]],
    filter_questions: List[Dict[str, Any]],
    filter_answers: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    매우 단순한 필터링 규칙:
    - 질문이 yesno이고, 답이 "아니오"면
      affects_jobs에 포함된 직무를 제거
    """
    removed_titles = set()

    for q in filter_questions:
        qid = q["id"]
        ans = filter_answers.get(qid)

        if q["type"] == "yesno":
            if ans == "아니오":
                for jt in q["affects_jobs"]:
                    removed_titles.add(jt)

        # choice형은 단순 MVP에서는 제거하지 않고,
        # 이후 확장 가능하도록 둠.

    final = []
    for j in jobs:
        if j["job_title"] not in removed_titles:
            final.append(j)

    return final


# =========================================================
# 4페이지: 로드맵 생성 (OpenAI 기반, 웹검색 없이)
# =========================================================
def generate_roadmap(job_title: str, user_answers: Dict[str, Any]) -> Dict[str, Any]:
    system = """
너는 커리어 로드맵 설계 AI다.
사용자가 선택한 직무를 기준으로,
한국 취업 시장에서 현실적인 2년 로드맵을 만든다.

주의:
- 웹 검색을 하지 않는다.
- 대신 일반적으로 알려진 업계 상식 수준에서 현실적인 계획을 제시한다.
- 너무 단정하지 말고, "예시"임을 분명히 한다.

반드시 JSON으로만 출력하라.
"""

    user = f"""
사용자가 선택한 직무: {job_title}
사용자 정보:
{json.dumps(user_answers, ensure_ascii=False, indent=2)}

요구사항:
- 시간축 3구간으로 나누기:
  1) 지금~3개월
  2) 3~12개월
  3) 1~2년
- 각 구간마다 해야 할 행동 4~6개 (현실적으로)
- 결과는 "로드맵 카드"처럼 보여줄 수 있게 구성

출력 JSON 스키마:
{{
  "headline": "예비 OO의 이제뭐하지",
  "disclaimer": "이 로드맵은 예시이며 ...",
  "timeline": [
    {{
      "period": "지금~3개월",
      "milestones": ["...", "..."]
    }},
    {{
      "period": "3~12개월",
      "milestones": ["...", "..."]
    }},
    {{
      "period": "1~2년",
      "milestones": ["...", "..."]
    }}
  ],
  "recommended_resources": ["추천 리소스 1", "추천 리소스 2", "추천 리소스 3"]
}}
"""

    data = openai_chat_json(system=system, user=user)
    return data


# =========================================================
# 페이지 1: 첫 접속 화면
# =========================================================
def render_page_1():
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)

    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown(
            f"<h1 style='text-align:center;'>{APP_TITLE}</h1>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        st.session_state.api_key = st.text_input(
            "api 키 입력란",
            value=st.session_state.api_key,
            type="password",
            placeholder="OpenAI API Key를 입력하세요",
            label_visibility="collapsed",
        )

        st.caption("※ 키는 서버에 저장되지 않고 현재 세션에서만 사용됩니다.")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("시작하기 →", use_container_width=True, disabled=(st.session_state.api_key.strip() == "")):
                go(2)


# =========================================================
# 페이지 2: 사용자 정보 입력
# =========================================================
def render_page_2():
    st.title("2. 사용자 정보 입력")
    st.write("질문에 답하면, 당신에게 맞는 직무를 추천해줄게요.")

    st.markdown("---")

    with st.form("user_form"):
        render_user_questions_form()
        submitted = st.form_submit_button("추천 받기 →", use_container_width=True)

    if submitted:
        if st.session_state.api_key.strip() == "":
            st.error("API 키가 필요해요. 1페이지에서 입력해 주세요.")
            return

        with st.spinner("사용자 정보를 분석 중... (OpenAI 호출)"):
            try:
                jobs = generate_job_recommendations(st.session_state.user_answers)
                st.session_state.job_reco = jobs

                filter_qs = generate_filter_questions(jobs)
                st.session_state.filter_questions = filter_qs

                # 필터 답변 초기화
                st.session_state.filter_answers = {}
                go(3)

            except Exception as e:
                st.error("추천 생성 중 오류가 발생했어요.")
                st.exception(e)


    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        if st.button("← 이전", use_container_width=True):
            go(1)


# =========================================================
# 페이지 3: 추천 직무 + 필터링 질문 + 최종 선택
# =========================================================
def render_page_3():
    st.title("3. 사용자 정보 분석 및 제안")

    if not st.session_state.job_reco:
        st.warning("추천 직무가 아직 생성되지 않았어요. 2페이지부터 진행해 주세요.")
        if st.button("2페이지로 이동"):
            go(2)
        return

    left, right = st.columns([1, 1])

    # 좌측: 추천 직무 리스트
    with left:
        st.subheader("추천 직무 리스트")
        st.caption("OpenAI가 사용자 입력 기반으로 생성한 추천입니다.")

        for j in st.session_state.job_reco:
            with st.container(border=True):
                st.markdown(f"### {j['job_title']}")
                st.write(f"**분야:** {j.get('category', '-')}")
                st.write(j.get("why_fit", ""))
                st.caption(f"요구조건 힌트: {j.get('requirements_hint', '-')}")


    # 우측: 필터 질문 + 최종 추천
    with right:
        st.subheader("추천 직무 중, 내가 가능한 직무만 남기기")

        if not st.session_state.filter_questions:
            st.info("현재 직무 리스트에서 특별한 조건 질문이 필요하지 않아 보입니다.")
        else:
            st.write("아래 질문에 답하면, 현실적으로 불가능한 직무는 자동으로 제외돼요.")

        with st.form("filter_form"):
            for q in st.session_state.filter_questions:
                st.markdown(f"**{q['question']}**")

                if q["type"] == "yesno":
                    ans = st.radio(
                        q["id"],
                        q["options"],
                        horizontal=True,
                        label_visibility="collapsed",
                        index=0
                    )
                else:
                    ans = st.selectbox(
                        q["id"],
                        q["options"],
                        label_visibility="collapsed",
                    )

                st.session_state.filter_answers[q["id"]] = ans
                st.caption(f"영향 직무: {', '.join(q['affects_jobs'])}")

                st.write("")

            submitted = st.form_submit_button("필터 적용하기", use_container_width=True)

        if submitted or st.session_state.final_jobs:
            st.session_state.final_jobs = apply_filtering(
                jobs=st.session_state.job_reco,
                filter_questions=st.session_state.filter_questions,
                filter_answers=st.session_state.filter_answers,
            )

        st.markdown("---")

        if st.session_state.final_jobs:
            st.success("최종 추천 직무 리스트가 완성됐어요. 아래에서 하나를 선택해 주세요.")

            job_titles = [j["job_title"] for j in st.session_state.final_jobs]
            st.session_state.selected_job = st.radio(
                "최종 직무 선택",
                options=job_titles,
                label_visibility="collapsed",
            )

            st.markdown("---")

            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                if st.button("← 이전", use_container_width=True):
                    go(2)
            with col_c:
                if st.button("다음 →", use_container_width=True, disabled=(st.session_state.selected_job is None)):
                    go(4)

        else:
            st.info("아직 필터 적용 결과가 없어요. 위 질문에 답하고 필터를 적용해 주세요.")

            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                if st.button("← 이전", use_container_width=True):
                    go(2)


# =========================================================
# 페이지 4: 선택 직무 로드맵
# =========================================================
def render_page_4():
    st.title("4. 최종 진로 로드맵 제시")

    if not st.session_state.selected_job:
        st.warning("선택한 직무가 없어요. 3페이지에서 직무를 선택해 주세요.")
        if st.button("3페이지로 이동"):
            go(3)
        return

    job = st.session_state.selected_job

    st.markdown(f"### {job}를 선택하셨습니다!")
    st.markdown(f"## 예비 {job}의 **{APP_TITLE}**")

    st.markdown("---")

    # 로드맵 생성 버튼
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("로드맵 생성하기 (OpenAI)", use_container_width=True):
            with st.spinner("로드맵을 생성 중..."):
                try:
                    st.session_state.roadmap = generate_roadmap(job, st.session_state.user_answers)
                except Exception as e:
                    st.error("로드맵 생성 중 오류가 발생했어요.")
                    st.exception(e)

    with col_b:
        if st.button("다른 직무 다시 고르기", use_container_width=True):
            st.session_state.roadmap = None
            go(3)

    st.markdown("---")

    if st.session_state.roadmap:
        roadmap = st.session_state.roadmap

        st.info(roadmap.get("disclaimer", "이 로드맵은 예시입니다."))

        timeline = roadmap.get("timeline", [])
        for t in timeline:
            with st.container(border=True):
                st.subheader(t.get("period", "기간"))
                for m in t.get("milestones", []):
                    st.write(f"🔘 {m}")

        st.markdown("### 추천 리소스")
        for r in roadmap.get("recommended_resources", []):
            st.write(f"- {r}")

    else:
        st.caption("아직 로드맵이 생성되지 않았어요. 위 버튼을 눌러주세요.")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← 이전", use_container_width=True):
            go(3)
    with col3:
        if st.button("처음으로", use_container_width=True):
            # 초기화 느낌
            st.session_state.page = 1
            st.session_state.user_answers = {}
            st.session_state.job_reco = []
            st.session_state.filter_questions = []
            st.session_state.filter_answers = {}
            st.session_state.final_jobs = []
            st.session_state.selected_job = None
            st.session_state.roadmap = None
            go(1)


# =========================================================
# 라우터
# =========================================================
def render_router():
    if st.session_state.page == 1:
        render_page_1()
    elif st.session_state.page == 2:
        render_page_2()
    elif st.session_state.page == 3:
        render_page_3()
    elif st.session_state.page == 4:
        render_page_4()
    else:
        go(1)
        render_page_1()


render_router()



