import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

session = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")

# agent : 최초 1번만 생성
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name = "ChatGPT Clone",
        instructions = """
        당신은 도움이 되는 조수입니다.

        당신은 다음 tool에 접근할 수 있습니다:
            - Web Search Tool : 사용자가 당신의 학습 데이터에 없는 질문을 할 때 사용하세요. 이 도구를 이용해 최신 사건이나 현재 정보를 확인할 수 있습니다.
        """,
        tools = [
            WebSearchTool()
        ]
    )

agent = st.session_state["agent"]

# 세션 : 최초 1번만 초기화
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db"
    )

session = st.session_state["session"]

# 이전 대화 내용 보여주기
async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔎 Searched the web...")

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": ("🔎 Starting web search...", "running"),
        "response.web_search_call.searching": ("🔎 Web search in progress...", "running"),
        "response.completed": ("", "complete")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label = label, state = state)

# 채팅으로 전달받은 내용 agent로 전달 + 응답값 화면 노출
async def run_agent(message):
    with st.chat_message("assistant"):
        status_container = st.status("⌛", expanded = False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent, 
            message,
            session = session
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response)

############################################
#################### UI ####################
############################################

prompt = st.chat_input("Write a message for your assistant")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    asyncio.run(run_agent(prompt))

with st.sidebar:
    reset = st.button("Reset memory")

    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))