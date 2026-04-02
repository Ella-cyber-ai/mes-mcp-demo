import streamlit as st
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import json

# 환경변수 로드
load_dotenv(override=True)
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# MCP Tool 불러오기
sys.path.insert(0, os.path.dirname(__file__))
from mcp_server.server import (
    get_production,
    get_defect_analysis,
    get_equipment_status,
    get_daily_report
)

TOOLS = {
    "get_production": get_production,
    "get_defect_analysis": get_defect_analysis,
    "get_equipment_status": get_equipment_status,
    "get_daily_report": get_daily_report,
}

# Groq Tool 정의
groq_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_production",
            "description": "생산 실적을 조회합니다. 날짜나 라인별 생산량, 달성률을 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_date": {"type": "string", "description": "날짜 (YYYY-MM-DD). 오늘 전체 조회 시 오늘 날짜 입력"},
                    "line_name": {"type": "string", "description": "라인명 (A라인, B라인, C라인). 전체 조회 시 생략"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_defect_analysis",
            "description": "불량률을 분석합니다. 라인별 불량 유형과 건수를 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year_month": {"type": "string", "description": "연월 (YYYY-MM)"},
                    "line_name": {"type": "string", "description": "라인명 (A라인, B라인, C라인)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_equipment_status",
            "description": "설비 가동률을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_date": {"type": "string", "description": "날짜 (YYYY-MM-DD)"},
                    "line_name": {"type": "string", "description": "라인명"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_report",
            "description": "일일 생산 보고서를 생성합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_date": {"type": "string", "description": "날짜 (YYYY-MM-DD)"}
                },
                "required": ["work_date"]
            }
        }
    }
]

def chat_with_mes(user_message):
    try:
        today = datetime.today().strftime("%Y-%m-%d")
        messages = [
            {
                "role": "system",
                "content": f"""당신은 제조회사 MES 데이터 분석 AI 어시스턴트입니다.
직원들의 질문에 한국어로 친절하게 답변해 주세요.
데이터 조회 시 반드시 Tool을 활용하고 결과를 보기 좋게 정리해 주세요.
오늘 날짜는 {today} 입니다."""
            },
            {"role": "user", "content": user_message}
        ]

        # 첫 번째 Groq 호출
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            max_tokens=2000
        )

        # Tool 호출 처리 루프
        max_iterations = 5
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            msg = response.choices[0].message

            # Tool 호출 없으면 최종 답변 반환
            if not msg.tool_calls:
                return msg.content

            # Tool 호출 처리
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls
                ]
            })

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments)
                tool_result = str(TOOLS[tool_name](**tool_args)) if tool_name in TOOLS else "알 수 없는 Tool"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result
                })

            # Tool 결과 포함해서 다시 호출
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=groq_tools,
                tool_choice="auto",
                max_tokens=2000
            )

        return response.choices[0].message.content

    except Exception as e:
        return f"오류: {str(e)}"

# ── Streamlit UI ───────────────────────────────

st.set_page_config(
    page_title="MES AI 어시스턴트",
    page_icon="🏭",
    layout="centered"
)

st.title("🏭 MES AI 어시스턴트")
st.caption("MCP 기반 스마트 제조 데이터 조회 · Powered by Groq")

# 채팅 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! MES 데이터 AI 어시스턴트입니다.\n생산 실적, 불량률, 설비 현황 등 궁금한 것을 편하게 물어보세요 😊"}
    ]

if "quick_input" not in st.session_state:
    st.session_state.quick_input = None

# 빠른 질문 버튼
st.markdown("**빠른 질문**")
quick_questions = [
    ("📊 불량률 분석", "이번달 불량률 높은 라인 순서로 보여줘"),
    ("🏭 생산량 조회", "오늘 전체 라인 생산량 알려줘"),
    ("🔍 불량 원인",  "B라인 불량 원인 TOP 3 알려줘"),
    ("📋 일일 보고서", "오늘 일일 보고서 작성해줘"),
]

cols = st.columns(4)
for i, (label, question) in enumerate(quick_questions):
    if cols[i].button(label, key=f"quick_btn_{i}", use_container_width=True):
        st.session_state.quick_input = question

# 채팅 히스토리 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 빠른 질문 처리
if st.session_state.quick_input:
    prompt = st.session_state.quick_input
    st.session_state.quick_input = None
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            response = chat_with_mes(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# 일반 입력
if prompt := st.chat_input("예: 이번달 B라인 불량률 분석해줘"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            response = chat_with_mes(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()