import dotenv
import asyncio

dotenv.load_dotenv()

from agents import Agent, Runner, SQLiteSession, function_tool, trace
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel

# session_id : 세션 식별 구분자
# db path : 세션 저장소 위치 (기본값 : ":memory:" - 일회성 세션)
session = SQLiteSession("user_1", "ai-memory.db")

class Answer(BaseModel):
    answer: str
    background_explanation: str

@function_tool
def get_weather():
    return "30"


geography_agent = Agent(
    name = "Geo Expert Agent",
    instructions = "당신은 지리 전문가로서, 지리에 관한 모든 질문에 전문적으로 답변합니다.",
    # handoff 발생 조건 설명
    handoff_description = "이 Agent를 사용하여 지리와 관련된 질문에 답변하세요.",
    tools = [
        get_weather
    ],
    output_type = Answer
)

economics_agent = Agent(
    name = "Economics Expert Agent",
    instructions = "당신은 경제 전문가로서, 경제에 관한 모든 질문에 전문적으로 답변합니다.",
    # handoff 발생 조건 설명
    handoff_description = "이 Agent를 사용하여 경제와 관련된 질문에 답변하세요."
)

main_agent = Agent(
    name = "Main Agent",
    instructions = "당신은 사용자와 대화하는 Agent입니다. 사용자의 질문을 처리하기에 가장 적합한 에이전트에게 제어권을 넘겨야 합니다.",
    # handoff : 현재 대화 Agent가 다른 전문 Agent에게 대화 주도권을 넘김
    handoffs = [
        geography_agent,
        economics_agent
    ]
)

async def main():
    # agent 구동에 대한 도식화
    # 연결된 agent / agent에서 호출 가능한 tools 등
    # 그냥 .py 파일에서는 실행해도 새로운 파일이 생기거나 도식화 되지 않음
    # 찾아보니 Jupyter Notebook용 시각화 함수인 듯?
    # draw_graph(main_agent)

    # run : 최종 처리 내역 리턴
    # run_sync : await를 사용하지 못하거나 사용하지 않고 싶을 때 (run과 결과값 동일)
    # run_streamed : 실시간으로 처리 내역 리턴
    # trace를 그룹별로 보고 싶은 경우, trace("그룹명")
    with trace("user_1"):
        result = await Runner.run(
            # starting agent
            main_agent,
            "태국 북부 지방의 수도는 어디야?",
            session = session,
        )

        result = await Runner.run(
            # starting agent
            main_agent,
            "미국의 수도는 어디야?",
            session = session,
        )

    print(result.last_agent.name)
    print(result.final_output)

# 실행
asyncio.run(main())