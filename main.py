import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession

session = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")

# agent : 최초 1번만 생성
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name = "ChatGPT Clone",
        instructions = """
        당신은 도움이 되는 조수입니다.
        """
    )

agent = st.session_state["agent"]

async def run_agent(message):
    stream = Runner.run_streamed(
        agent, 
        message,
        session = session
    )

    async for event in stream.stream_events():
        if event.type == "raw_response_event":
            if event.data.type == "response.output_text.delta":
                with st.chat_message("ai"):
                    st.write(event.data.delta)

############################################
#################### UI ####################
############################################

# 세션 : 최초 1번만 초기화
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db"
    )

session = st.session_state["session"]

prompt = st.chat_input("Write a message for your assistant")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    
    asyncio.run(run_agent(prompt))

with st.sidebar:
    reset = st.button("Reset memory")

    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))