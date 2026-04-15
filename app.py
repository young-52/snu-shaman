"""
🔮 샤:머니즘 (SHAMANISM)
서울대학교 학생을 위한 사주 기반 장소·음료 추천 서비스

Gradio 6.x | korean-lunar-calendar | HuggingFace Inference API
"""

import os
import gradio as gr
from datetime import datetime

from saju_engine import analyze_saju, format_saju_result
from recommender import build_system_prompt, create_initial_greeting, get_llm_response

# ── .env 파일 로드 (python-dotenv 없이) ──
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())


# ═══════════════════════════════════════════════════════
#  Custom CSS — 사주 추천 테마
# ═══════════════════════════════════════════════════════
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700;900&display=swap');

/* ── 전역 타이포그래피 ── */
.gradio-container {
    font-family: 'Noto Serif KR', serif !important;
}

/* ── 사이드바 스타일 ── */
.sidebar {
    background: linear-gradient(180deg, #1a0533 0%, #2d1b69 50%, #1a0533 100%) !important;
}

.sidebar .gr-block {
    border: none !important;
}

/* ── 앱 타이틀 ── */
#app-title {
    font-family: 'Noto Serif KR', serif !important;
    font-size: 2rem !important;
    font-weight: 900 !important;
    text-align: center !important;
    background: linear-gradient(135deg, #c084fc, #818cf8, #60a5fa) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    padding: 8px 0 !important;
    letter-spacing: 2px !important;
}

#app-subtitle {
    text-align: center !important;
    color: #a78bfa !important;
    font-size: 0.9rem !important;
    margin-top: -8px !important;
    font-family: 'Noto Serif KR', serif !important;
}

/* ── 분석 결과 마크다운 ── */
#saju-result {
    font-family: 'Noto Serif KR', serif !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(99, 102, 241, 0.05)) !important;
}

#saju-result h2 {
    font-family: 'Noto Serif KR', serif !important;
    color: #c084fc !important;
}

#saju-result table {
    width: 100% !important;
    border-collapse: collapse !important;
}

#saju-result th, #saju-result td {
    padding: 8px !important;
    text-align: center !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
}

#saju-result blockquote {
    border-left: 3px solid #c084fc !important;
    background: rgba(192, 132, 252, 0.1) !important;
    padding: 12px !important;
    border-radius: 0 8px 8px 0 !important;
}

/* ── 분석 버튼 ── */
#analyze-btn {
    background: linear-gradient(135deg, #7c3aed, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-family: 'Noto Serif KR', serif !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 1px !important;
}

#analyze-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6) !important;
}

/* ── 챗봇 영역 ── */
.chatbot .message {
    font-family: 'Noto Serif KR', serif !important;
}

.chatbot .bot .message-content {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(99, 102, 241, 0.1)) !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
}

/* ── 입력 필드 커스텀 ── */
.sidebar input, .sidebar select {
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 8px !important;
    background: rgba(26, 5, 51, 0.3) !important;
}

.sidebar input:focus, .sidebar select:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
}

/* ── 사이드바 내 라벨 색상 ── */
.sidebar label {
    color: #c4b5fd !important;
    font-weight: 500 !important;
}

/* 마크다운 스타일 (채팅 내) */
.chatbot .bot .message-content strong {
    color: #c084fc !important;
}
"""

# ═══════════════════════════════════════════════════════
#  Gradio 테마 설정 (Soft 기반 커스텀)
# ═══════════════════════════════════════════════════════
shamanism_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.purple,
    secondary_hue=gr.themes.colors.indigo,
    neutral_hue=gr.themes.colors.slate,
    font=gr.themes.GoogleFont("Noto Serif KR"),
    font_mono=gr.themes.GoogleFont("Fira Code"),
).set(
    # 배경색
    body_background_fill="linear-gradient(180deg, #0f0a1e 0%, #1a1035 50%, #0f0a1e 100%)",
    body_background_fill_dark="linear-gradient(180deg, #0f0a1e 0%, #1a1035 50%, #0f0a1e 100%)",
    # 블록 배경
    block_background_fill="rgba(26, 16, 53, 0.6)",
    block_background_fill_dark="rgba(26, 16, 53, 0.6)",
    block_border_width="1px",
    block_border_color="rgba(139, 92, 246, 0.15)",
    block_border_color_dark="rgba(139, 92, 246, 0.15)",
    block_shadow="0 4px 30px rgba(139, 92, 246, 0.1)",
    block_shadow_dark="0 4px 30px rgba(139, 92, 246, 0.1)",
    block_radius="16px",
    # 입력 필드
    input_background_fill="rgba(30, 20, 60, 0.8)",
    input_background_fill_dark="rgba(30, 20, 60, 0.8)",
    input_border_color="rgba(139, 92, 246, 0.3)",
    input_border_color_dark="rgba(139, 92, 246, 0.3)",
    # 버튼
    button_primary_background_fill="linear-gradient(135deg, #7c3aed, #6366f1)",
    button_primary_background_fill_dark="linear-gradient(135deg, #7c3aed, #6366f1)",
    button_primary_text_color="white",
    button_primary_text_color_dark="white",
    # 텍스트 색상
    body_text_color="#e2d9f3",
    body_text_color_dark="#e2d9f3",
    block_title_text_color="#c4b5fd",
    block_title_text_color_dark="#c4b5fd",
    block_label_text_color="#a78bfa",
    block_label_text_color_dark="#a78bfa",
)


# ═══════════════════════════════════════════════════════
#  이벤트 핸들러
# ═══════════════════════════════════════════════════════
def on_analyze(year, month, day, hour, user_saju_state):
    """사주 분석 버튼 클릭 시 호출."""
    try:
        year = int(year)
        month = int(month)
        day = int(day)
        hour = int(hour)
    except (ValueError, TypeError):
        return (
            "⚠️ 생년월일시를 올바르게 입력해 주세요.",
            user_saju_state,
            gr.update(),  # chatbot
            [],  # history
        )

    # 사주 분석
    result = analyze_saju(year, month, day, hour)
    formatted = format_saju_result(result)

    # 시스템 프롬프트 빌드 & 상태 저장
    system_prompt = build_system_prompt(result)
    user_saju_state = {
        "analyzed": True,
        "result": result,
        "system_prompt": system_prompt,
    }

    # 첫 인사말 생성 (정적)
    greeting = create_initial_greeting(result)
    initial_history = [{"role": "assistant", "content": greeting}]

    return (
        formatted,
        user_saju_state,
        initial_history,
        initial_history,
    )


def on_chat(message, history, user_saju_state, hf_token: gr.OAuthToken | None = None):
    """챗봇 메시지 전송 시 호출."""
    if not user_saju_state or not user_saju_state.get("analyzed"):
        yield history + [
            {"role": "user", "content": message},
            {
                "role": "assistant",
                "content": "🔮 먼저 사이드바에서 생년월일시를 입력하고 **[사주 분석하기]** 버튼을 눌러주세요!",
            },
        ]
        return

    # 토큰 결정: OAuth 토큰 → 환경변수 HF_TOKEN fallback
    import os

    raw_token = hf_token.token if hf_token else None
    env_token = os.environ.get("HF_TOKEN", "").strip()
    effective_token = raw_token or env_token

    if not effective_token:
        yield history + [
            {"role": "user", "content": message},
            {
                "role": "assistant",
                "content": "🔑 Hugging Face 토큰이 필요합니다.\n\n사이드바에서 로그인하거나, `.env` 파일에 `HF_TOKEN`을 설정해 주세요.",
            },
        ]
        return

    system_prompt = user_saju_state["system_prompt"]
    new_history = history + [{"role": "user", "content": message}]

    # 스트리밍 응답
    for partial in get_llm_response(
        message=message,
        history=new_history[:-1],  # 마지막 user 메시지 제외 (함수 내에서 추가)
        system_prompt=system_prompt,
        hf_token=effective_token,
    ):
        yield new_history + [{"role": "assistant", "content": partial}]


# ═══════════════════════════════════════════════════════
#  Gradio UI 구성 (Blocks + Sidebar)
# ═══════════════════════════════════════════════════════
now = datetime.now()

with gr.Blocks(title="샤:머니즘 — 관악의 기운을 읽다") as demo:
    # ── State 관리 ──
    user_saju_state = gr.State(value=None)
    chat_history = gr.State(value=[])

    # ── 사이드바: 입력부 ──
    with gr.Sidebar():
        gr.Markdown(
            "# 🔮 샤:머니즘",
            elem_id="app-title",
        )
        gr.Markdown(
            "*관악의 기운을 읽다*",
            elem_id="app-subtitle",
        )

        gr.LoginButton(value="🔑 Hugging Face 로그인")

        gr.Markdown("---")
        gr.Markdown("### 📅 사주 입력")

        with gr.Row():
            year_input = gr.Number(
                label="태어난 해",
                value=2000,
                minimum=1950,
                maximum=2025,
                precision=0,
                elem_id="year-input",
            )
            month_input = gr.Dropdown(
                label="월",
                choices=list(range(1, 13)),
                value=1,
                elem_id="month-input",
            )
        with gr.Row():
            day_input = gr.Dropdown(
                label="일",
                choices=list(range(1, 32)),
                value=1,
                elem_id="day-input",
            )
            # 시간대별 지지 라벨
            _HOUR_LABELS = [
                "23-01시 (子)",
                "01-03시 (丑)",
                "03-05시 (寅)",
                "05-07시 (卯)",
                "07-09시 (辰)",
                "09-11시 (巳)",
                "11-13시 (午)",
                "13-15시 (未)",
                "15-17시 (申)",
                "17-19시 (酉)",
                "19-21시 (戌)",
                "21-23시 (亥)",
            ]
            hour_input = gr.Dropdown(
                label="태어난 시",
                choices=[(f"{h:02d}시", h) for h in range(24)],
                value=12,
                elem_id="hour-input",
            )

        analyze_btn = gr.Button(
            "🔮 사주 분석하기",
            variant="primary",
            elem_id="analyze-btn",
        )

        gr.Markdown("---")

        saju_result_display = gr.Markdown(
            value=("> *생년월일시를 입력하고 분석 버튼을 눌러주세요.* 🌙"),
            elem_id="saju-result",
        )

    # ── 메인 영역: 챗봇 ──
    chatbot = gr.Chatbot(
        value=[],
        label="🔮 샤:머니즘",
        placeholder=(
            "✨ 사주 기반 캠퍼스 추천 서비스에 오신 것을 환영합니다.\n\n"
            "← 왼쪽 사이드바에서 생년월일시를 입력하고\n"
            "**[🔮 사주 분석하기]** 버튼을 눌러 시작하세요."
        ),
        height=600,
        buttons=["copy", "copy_all"],
        avatar_images=(
            None,
            "https://em-content.zobj.net/source/twitter/376/crystal-ball_1f52e.png",
        ),
    )

    msg_input = gr.Textbox(
        placeholder="무엇이든 물어보세요! (예: 오늘 공부하기 좋은 곳은?)",
        show_label=False,
        container=False,
        elem_id="msg-input",
    )

    # ── 이벤트 연결 ──
    analyze_btn.click(
        fn=on_analyze,
        inputs=[year_input, month_input, day_input, hour_input, user_saju_state],
        outputs=[saju_result_display, user_saju_state, chatbot, chat_history],
    )

    msg_input.submit(
        fn=on_chat,
        inputs=[msg_input, chatbot, user_saju_state],
        outputs=[chatbot],
    ).then(
        fn=lambda: "",
        outputs=[msg_input],
    )


if __name__ == "__main__":
    demo.launch(
        theme=shamanism_theme,
        css=CUSTOM_CSS,
    )
