import dotenv

dotenv.load_dotenv()

from openai import OpenAI
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

client = OpenAI()

VECTOR_STORE_ID = "vs_68f4ed311c008191b484ebea1fe8edbe"

session = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")

# agent : 최초 1번만 생성
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name = "ChatGPT Clone",
        instructions = """
        당신은 도움이 되는 조수입니다.

        당신은 다음 tool에 접근할 수 있습니다:
            - Web Search Tool : 사용자가 당신의 학습 데이터에 없는 질문을 할 때 사용하세요. 이 도구를 이용해 최신 사건이나 현재 정보를 확인할 수 있습니다.
            - File Search Tool : 사용자가 자신과 관련된 사실에 대해 묻거나, 특정 파일에 대한 질문을 할 때 이 도구를 사용하세요.
        """,
        tools = [
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids = [
                    VECTOR_STORE_ID
                ],
                # 파일이 여러개 있을 때, 상위 3개 파일만 가져옴
                max_num_results = 3
            )
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
                        # escape sequence가 잘못 인식돼서 강의랑 다르게 \ > \\ 로 처리
                        st.write(message["content"][0]["text"].replace("$", "\\$"))
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔎 Searched the web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🔎 Searched the files...")

asyncio.run(paint_history())

# open ai 응답 data.type에 따른 status 업데이트
def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": ("🔎 Starting web search...", "running"),
        "response.web_search_call.searching": ("🔎 Web search in progress...", "running"),
        "response.file_search_call.completed": ("✅ File search completed.", "complete"),
        "response.file_search_call.in_progress": ("📁 Starting file search...", "running"),
        "response.file_search_call.searching": ("📁 File search in progress...", "running"),
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
                        text_placeholder.write(response.replace("$", "\\$"))

############################################
#################### UI ####################
############################################

prompt = st.chat_input(
    "Write a message for your assistant",
    # 확장자 txt의 파일 업로드 허용
    accept_file = True,
    file_type = ["txt"]
)

if prompt:

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⌛ Uploading file...") as status:
                    uploaded_file = client.files.create(
                        file = (file.name, file.getvalue()),
                        purpose = "user_data"
                    )

                    status.update(label = "⌛ Attaching file...")

                    client.vector_stores.files.create(
                        vector_store_id = VECTOR_STORE_ID,
                        file_id = uploaded_file.id
                    )

                    status.update(label = "File uploaded", state = "complete")

    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)

        asyncio.run(run_agent(prompt.text))

with st.sidebar:
    reset = st.button("Reset memory")

    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))