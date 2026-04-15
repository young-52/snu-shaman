"""
🔮 Geoman-ji: The Saju Logic Architect
사주(四柱) 분석 엔진 — 생년월일시를 기반으로 부족한 오행을 도출한다.

korean-lunar-calendar를 사용하여 천간·지지를 구한 후,
각 글자에 매핑된 오행을 집계하여 가장 부족한 기운을 찾는다.
"""

from korean_lunar_calendar import KoreanLunarCalendar

# ── 천간(天干) → 오행 매핑 ──
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEONGAN_ELEMENT = {
    "갑": "木",
    "을": "木",
    "병": "火",
    "정": "火",
    "무": "土",
    "기": "土",
    "경": "金",
    "신": "金",
    "임": "水",
    "계": "水",
}

# ── 지지(地支) → 오행 매핑 ──
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JIJI_ELEMENT = {
    "자": "水",
    "축": "土",
    "인": "木",
    "묘": "木",
    "진": "土",
    "사": "火",
    "오": "火",
    "미": "土",
    "신": "金",
    "유": "金",
    "술": "土",
    "해": "水",
}

# ── 시간 → 시주(時柱) 지지 매핑 (2시간 단위) ──
HOUR_TO_JIJI = {
    23: "자",
    0: "자",
    1: "축",
    2: "축",
    3: "인",
    4: "인",
    5: "묘",
    6: "묘",
    7: "진",
    8: "진",
    9: "사",
    10: "사",
    11: "오",
    12: "오",
    13: "미",
    14: "미",
    15: "신",
    16: "신",
    17: "유",
    18: "유",
    19: "술",
    20: "술",
    21: "해",
    22: "해",
}

# ── 일간(日干) 기준 시간 천간 결정 표 ──
# 일간의 천간 인덱스(0-9) % 5 에 따라 자시(子)의 천간이 결정됨
# 갑·기일 → 갑자시, 을·경일 → 병자시, 병·신일 → 무자시, 정·임일 → 경자시, 무·계일 → 임자시
HOUR_STEM_BASE = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}

# 오행 한글 이름
ELEMENT_NAMES = {
    "木": "나무(木)",
    "火": "불(火)",
    "土": "흙(土)",
    "金": "쇠(金)",
    "水": "물(水)",
}

# 오행 색상 (UI 표시용)
ELEMENT_COLORS = {
    "木": "#4CAF50",
    "火": "#FF5722",
    "土": "#FFC107",
    "金": "#9E9E9E",
    "水": "#2196F3",
}

# 오행 이모지
ELEMENT_EMOJI = {
    "木": "🌳",
    "火": "🔥",
    "土": "⛰️",
    "金": "⚔️",
    "水": "💧",
}


def _get_gap_ja(year: int, month: int, day: int) -> str:
    """양력 날짜에 대한 간지 문자열을 반환한다 (예: '정유년 병오월 임오일')."""
    cal = KoreanLunarCalendar()
    cal.setSolarDate(year, month, day)
    return cal.getGapJaString()


def _parse_gap_ja(gap_ja_str: str) -> list[tuple[str, str]]:
    """
    간지 문자열을 파싱하여 [(천간, 지지), ...] 리스트를 반환한다.
    예: '정유년 병오월 임오일' → [('정','유'), ('병','오'), ('임','오')]
    """
    pillars = []
    for token in gap_ja_str.split():
        # 각 토큰은 'XY년', 'XY월', 'XY일' 형태
        clean = token.rstrip("년월일")
        if len(clean) >= 2:
            pillars.append((clean[0], clean[1]))
    return pillars


def _compute_hour_pillar(day_stem: str, hour: int) -> tuple[str, str]:
    """
    일간(day_stem)과 태어난 시(hour, 0-23)로부터 시주의 (천간, 지지)를 계산한다.
    """
    # 일간의 인덱스
    day_stem_idx = CHEONGAN.index(day_stem)
    base_group = day_stem_idx % 5
    # 자시(子)의 천간 인덱스
    zi_stem_idx = HOUR_STEM_BASE[base_group]
    # 해당 시간의 지지
    jiji = HOUR_TO_JIJI[hour]
    jiji_idx = JIJI.index(jiji)
    # 시간 천간 = 자시_천간 + 지지_순서
    hour_stem_idx = (zi_stem_idx + jiji_idx) % 10
    return CHEONGAN[hour_stem_idx], jiji


def analyze_saju(year: int, month: int, day: int, hour: int) -> dict:
    """
    사주 분석 메인 함수.

    Parameters
    ----------
    year : 태어난 해 (양력)
    month : 태어난 월 (양력)
    day : 태어난 일 (양력)
    hour : 태어난 시 (0-23)

    Returns
    -------
    dict with keys:
        pillars: list of (천간, 지지) — 4주
        pillar_labels: list of str — ['년주', '월주', '일주', '시주']
        element_count: dict — {'木': n, '火': n, '土': n, '金': n, '水': n}
        weakest: str — 가장 부족한 오행 (한자)
        weakest_name: str — 가장 부족한 오행 (한글)
        strongest: str — 가장 강한 오행 (한자)
        gap_ja_str: str — 원본 간지 문자열
    """
    # 1) 년주·월주·일주 간지 구하기
    gap_ja_str = _get_gap_ja(year, month, day)
    pillars_3 = _parse_gap_ja(gap_ja_str)

    # 2) 시주 계산
    if len(pillars_3) >= 3:
        day_stem = pillars_3[2][0]  # 일간
    else:
        day_stem = "갑"  # fallback
    hour_pillar = _compute_hour_pillar(day_stem, hour)

    # 3) 4주 완성
    pillars = pillars_3 + [hour_pillar]
    pillar_labels = ["년주", "월주", "일주", "시주"]

    # 4) 오행 집계 (8자 각각)
    element_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for stem, branch in pillars:
        if stem in CHEONGAN_ELEMENT:
            element_count[CHEONGAN_ELEMENT[stem]] += 1
        if branch in JIJI_ELEMENT:
            element_count[JIJI_ELEMENT[branch]] += 1

    # 5) 부족한 오행·강한 오행
    weakest = min(element_count, key=element_count.get)
    strongest = max(element_count, key=element_count.get)

    # 시주를 포함한 문자열 재조합
    hour_stem, hour_branch = hour_pillar
    full_gap_ja = f"{gap_ja_str} {hour_stem}{hour_branch}시"

    return {
        "pillars": pillars,
        "pillar_labels": pillar_labels,
        "element_count": element_count,
        "weakest": weakest,
        "weakest_name": ELEMENT_NAMES[weakest],
        "strongest": strongest,
        "strongest_name": ELEMENT_NAMES[strongest],
        "gap_ja_str": full_gap_ja,
    }


def format_saju_result(result: dict) -> str:
    """
    사주 분석 결과를 마크다운 형식의 문자열로 포맷팅한다.
    """
    lines = []
    lines.append("## 🔮 사주 팔자 분석 결과\n")
    lines.append(f"**간지**: {result['gap_ja_str']}\n")

    # 사주 표
    lines.append("| 주 | 천간 | 지지 | 오행 |")
    lines.append("|:---:|:---:|:---:|:---:|")
    for label, (stem, branch) in zip(result["pillar_labels"], result["pillars"]):
        s_elem = CHEONGAN_ELEMENT.get(stem, "?")
        b_elem = JIJI_ELEMENT.get(branch, "?")
        lines.append(
            f"| {label} | {stem} ({ELEMENT_EMOJI.get(s_elem, '')} {s_elem}) "
            f"| {branch} ({ELEMENT_EMOJI.get(b_elem, '')} {b_elem}) "
            f"| {s_elem} · {b_elem} |"
        )

    # 오행 분포
    lines.append("\n### 오행 분포")
    total = sum(result["element_count"].values())
    for elem in ["木", "火", "土", "金", "水"]:
        count = result["element_count"][elem]
        bar = "█" * count + "░" * (total - count)
        lines.append(
            f"- {ELEMENT_EMOJI[elem]} **{ELEMENT_NAMES[elem]}**: {bar} ({count}/{total})"
        )

    lines.append(
        f"\n> 🌀 **부족한 기운**: {ELEMENT_EMOJI[result['weakest']]} "
        f"**{result['weakest_name']}** — 이 기운을 보하면 관악의 운이 트이리라!"
    )

    return "\n".join(lines)
