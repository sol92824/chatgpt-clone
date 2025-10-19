import dotenv
import asyncio

dotenv.load_dotenv()

from agents import Agent, Runner, SQLiteSession

# session_id : 세션 식별 구분자
# db path : 세션 저장소 위치 (기본값 : ":memory:" - 일회성 세션)
session = SQLiteSession("user_1", "ai-memory.db")

geography_agent = Agent(
    name = "Geo Expert Agent",
    instructions = "당신은 지리 전문가로서, 지리에 관한 모든 질문에 전문적으로 답변합니다.",
    # handoff 발생 조건 설명
    handoff_description = "이 Agent를 사용하여 지리와 관련된 질문에 답변하세요."
)

economics_agent = Agent(
    name = "Economics  Expert Agent",
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
    # run : 최종 처리 내역 리턴
    # run_sync : await를 사용하지 못하거나 사용하지 않고 싶을 때 (run과 결과값 동일)
    # run_streamed : 실시간으로 처리 내역 리턴
    result = await Runner.run(
        # starting agent
        main_agent,
        "국가들이 채권을 파는 이유가 뭐야?",
        session = session,
    )

    print(result.last_agent.name)
    print(result.final_output)

# 실행
asyncio.run(main())