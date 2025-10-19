import dotenv

dotenv.load_dotenv()

from openai import OpenAI
import asyncio
import base64
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool, CodeInterpreterTool, HostedMCPTool

client = OpenAI()

VECTOR_STORE_ID = "vs_68f4ed311c008191b484ebea1fe8edbe"

session = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")

# agent : 최초 1번만 생성
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        # 별도 인증절차를 거치지 않으면 권한 문제로 이미지 생성이 안됨
        # 버전을 낮추면 된다는 내용이 있어서 버전을 낮췄으나 지속적으로 에러남
        # 인증을 하고 싶지 않으므로 이미지 생성 테스트 X (ImageGenerationTool을 연결하면 다른 작업도 테스트 안되서 주석으로 변경)
        # model = "gpt-4o-mini",
        name = "ChatGPT Clone",
        instructions = """
        당신은 도움이 되는 조수입니다.

        당신은 다음 tool에 접근할 수 있습니다:
            - Web Search Tool : 사용자가 당신의 학습 데이터에 없는 질문을 할 때 사용하세요. 이 도구를 이용해 최신 사건이나 현재 정보를 확인할 수 있습니다.
            - File Search Tool : 사용자가 자신과 관련된 사실에 대해 묻거나, 특정 파일에 대한 질문을 할 때 이 도구를 사용하세요.
            - Code Interpreter Tool : 사용자의 질문에 답하기 위해 코드를 작성하고 실행해야 할 때 이 도구를 사용하세요.
        """,
        tools = [
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids = [
                    VECTOR_STORE_ID
                ],
                # 파일이 여러개 있을 때, 상위 3개 파일만 가져옴
                max_num_results = 3
            ),
            # ImageGenerationTool(
            #     tool_config = {
            #         "type": "image_generation",
            #         "quality": "low",
            #         "output_format": "jpeg",
            #         "moderation": "low",
            #         "partial_images": 1
            #     }
            # ),
            CodeInterpreterTool(
                tool_config = {
                    "type": "code_interpreter",
                    "container": {
                        "type": "auto",
                        # file_ids를 넘겨주면 해당 file에 대해 CodeInterpreterTool이 접근할 수 있는 권한을 주는 것
                        # 코드 생성시, import해서 사용 가능
                        # "file_ids": [...]
                    }
                }
            ),
            # MCP Tool : 외부 서버에 있는 문서나 소프트웨어 프로젝트 관련 자료를 조회/검색할 수 있는 도구
            HostedMCPTool(
                tool_config = {
                    "type": "mcp",
                    "server_url": "https://mcp.context7.com/mcp",
                    "server_label": "Context7",
                    "server_description": "Use this to get the docs from software projects.",
                    "require_approval": "never"
                }
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
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(message["content"])
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                else:
                    if message["type"] == "message":
                        # escape sequence가 잘못 인식돼서 강의랑 다르게 \ > \\ 로 처리
                        st.write(message["content"][0]["text"].replace("$", "\\$"))
        if "type" in message:
            message_type = message["type"]

            if message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔎 Searched the web...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🔎 Searched the files...")
            elif message_type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
            elif message_type == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.code(message["code"])
            elif message_type == "mcp_list_tools":
                with st.chat_message("ai"):
                    st.write(f"Listed {message["server_label"]}'s tools")
            elif message_type == "mcp_call":
                with st.chat_message("ai"):
                    st.write(f"Called {message["server_label"]}'s {message["name"]} with args {message["arguments"]}")


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
        "response.image_generation_call.generating": ("🎨 Drawing image...", "running"),
        "response.image_generation_call.in_progress": ("🎨 Drawing image...", "running"),
        "response.code_interpreter_call_code.done": ("🤖 Ran code.", "complete"),
        "response.code_interpreter_call_code.completed": ("🤖 Ran code.", "complete"),
        "response.code_interpreter_call_code.in_progress": ("🤖 Running code...", "complete"),
        "response.code_interpreter_call_code.interpreting": ("🤖 Running code...", "complete"),
        "response.mcp_call.completed": ("🛠️ Called MCP tool", "complete"),
        "response.mcp_call.failed": ("🛠️ Error calling MCP tool", "complete"),
        "response.mcp_call.in_progress": ("🛠️ Calling MCP tool", "running"),
        "response.mcp_list_tools.completed": ("🛠️ Listed MCP tools", "complete"),
        "response.mcp_list_tools.failed": ("🛠️ Error listing MCP tools", "complete"),
        "response.mcp_list_tools.in_progress": ("🛠️ Listing MCP tools", "running"),
        "response.completed": ("", "complete")
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label = label, state = state)

# 채팅으로 전달받은 내용 agent로 전달 + 응답값 화면 노출
async def run_agent(message):
    with st.chat_message("assistant"):
        status_container = st.status("⌛", expanded = False)
        code_placeholder = st.empty()
        image_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""
        code_response = ""

        st.session_state["code_placeholder"] = code_placeholder
        st.session_state["image_placeholder"] = image_placeholder
        st.session_state["text_placeholder"] = text_placeholder

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
                elif event.data.type == "response.code_interpreter_call_code.delta":
                    code_response += event.data.delta
                    code_placeholder.code(code_response)
                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)

############################################
#################### UI ####################
############################################

prompt = st.chat_input(
    "Write a message for your assistant",
    # 확장자 txt의 파일 업로드 허용
    accept_file = True,
    file_type = ["txt", "jpg", "jpeg", "png"]
)

if prompt:
    
    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

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

                    status.update(label = "✅ File uploaded", state = "complete")
        elif file.type.startswith("image/"):
            with st.status("⌛ Uploading image...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_data}"
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "detail": "auto",
                                        "image_url": data_uri
                                    }
                                ]
                            }
                        ]
                    )
                )
                status.update(label = "✅ Image uploaded", state = "complete")

            with st.chat_message("human"):
                st.image(data_uri)

    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)

        asyncio.run(run_agent(prompt.text))

with st.sidebar:
    reset = st.button("Reset memory")

    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))