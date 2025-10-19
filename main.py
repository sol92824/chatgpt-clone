import dotenv
import asyncio

dotenv.load_dotenv()

from agents import Agent, Runner, function_tool, SQLiteSession

# session_id : 세션 식별 구분자
# db path : 세션 저장소 위치 (기본값 : ":memory:" - 일회성 세션)
session = SQLiteSession("user_1", "ai-memory.db")

@function_tool
def get_weather(city : str) :
    """ 도시별 날씨 받아오기 """
    return "30도"

agent = Agent(
    name = "Assistant Agent",
    instructions = "당신은 유용한 Assistant입니다. 질문에 답할 때 필요하면 도구(tools)를 사용하세요.",
    tools = [ get_weather ],
)

async def main():
    # run : 최종 처리 내역 리턴
    # run_sync : await를 사용하지 못하거나 사용하지 않고 싶을 때 (run과 결과값 동일)
    # run_streamed : 실시간으로 처리 내역 리턴
    result = await Runner.run(
        agent,
        "안녕? 스페인 수도 날씨는 어때?",
        session = session
    )

    print(result.final_output)

# 실행
asyncio.run(main())