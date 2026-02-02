import streamlit as st
import requests

# ====================
# TMDB API 설정
# ====================
TMDB_API_KEY = "여기에_발급받은_API_KEY를_입력하세요"
BASE_URL = "https://api.themoviedb.org/3"

# 장르 맵핑 (TMDB 장르 ID 기준)
GENRE_MAP = {
    "로맨스/드라마": 18,   # Drama (예시)
    "액션/어드벤처": 28,  # Action
    "SF/판타지": 878,     # Science Fiction
    "코미디": 35          # Comedy
}

def fetch_movies_by_genre(genre_id):
    """장르별 영화 목록을 TMDB에서 가져오는 함수"""
    url = f"{BASE_URL}/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "with_genres": genre_id,
        "language": "ko-KR",
        "sort_by": "popularity.desc"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

# ====================
# Streamlit UI
# ====================
st.set_page_config(page_title="🎬 나와 어울리는 영화는?", layout="wide")
st.title("🎬 나와 어울리는 영화는?")
st.write("당신의 성향을 분석해 가장 잘 어울리는 영화를 추천해요! (TMDB 기반)")

# 질문
q1 = st.radio("1. 주말에 가장 하고 싶은 것은?",
              ["집에서 휴식", "친구와 놀기", "새로운 곳 탐험", "혼자 취미생활"])
q2 = st.radio("2. 스트레스 받으면?",
              ["혼자 있기", "수다 떨기", "운동하기", "맛있는 거 먹기"])
q3 = st.radio("3. 영화에서 중요한 것은?",
              ["감동 스토리", "시각적 영상미", "깊은 메시지", "웃는 재미"])
q4 = st.radio("4. 여행 스타일은?",
              ["계획적", "즉흥적", "액티비티", "힐링"])
q5 = st.radio("5. 친구 사이에서 나는?",
              ["듣는 역할", "주도하기", "분위기 메이커", "필요할 때 나타남"])

if st.button("🎯 결과 보기"):
    st.write("🎬 분석 중... 잠시만 기다려 주세요!")

    # ====================
    # 선택지를 장르 포인트로 변환
    # ====================
    responses = [q1, q2, q3, q4, q5]
    score = {
        "로맨스/드라마": 0,
        "액션/어드벤처": 0,
        "SF/판타지": 0,
        "코미디": 0
    }

    # 간단한 매핑 예제
    for r in responses:
        if "휴식" in r or "감동" in r or "듣는 역할" in r:
            score["로맨스/드라마"] += 1
        if "탐험" in r or "운동" in r or "액티비티" in r:
            score["액션/어드벤처"] += 1
        if "시각적" in r or "깊은" in r:
            score["SF/판타지"] += 1
        if "수다" in r or "웃는" in r:
            score["코미디"] += 1

    # 가장 높은 점수 장르
    favorite_genre = max(score, key=score.get)
    genre_id = GENRE_MAP.get(favorite_genre, 18)

    st.write(f"✨ 당신에게 어울리는 장르: **{favorite_genre}**")

    # ====================
    # 영화 추천 API 호출
    # ====================
    movies = fetch_movies_by_genre(genre_id)

    if movies:
        st.write("📽️ 추천 영화 목록:")
        for mv in movies[:8]:   # 상위 8개 보여주기
            title = mv.get("title")
            overview = mv.get("overview")
            poster_path = mv.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w200{poster_path}" if poster_path else ""

            st.markdown(f"#### {title}")
            if poster_url:
                st.image(poster_url)
            st.write(overview)
            st.write("---")
    else:
        st.write("추천 영화를 불러오는 데 문제가 발생했어요 🙇‍♀️")





