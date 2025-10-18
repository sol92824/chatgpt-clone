import dotenv
import asyncio

dotenv.load_dotenv()

from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city : str) :
    """ 도시별 날씨 받아오기 """
    return "30도"

agent = Agent(
    name = "Assistant Agent",
    instructions = "당신은 유용한 Assistant입니다. 질문에 답할 때 필요하면 도구(tools)를 사용하세요.",
    tools = [ get_weather ]
)

async def main():
    # run : 최종 처리 내역 리턴
    # run_streamed : 실시간으로 처리 내역 리턴
    stream = Runner.run_streamed(agent, "안녕? 스페인 수도 날씨는 어때?")

    # event.type
    # agent_updated_stream_event - agent 상태(state)나 속성(property)이 업데이트될 때 발생
    # run_item_stream_event - agent 업무 처리시 발생
    async for event in stream.stream_events():
        
        if event.type == "raw_response_event":
            continue
        elif event.type == "agent_updated_stream_event":
            print("Agent updated to", event.new_agent.name)
        elif event.type == "run_item_stream_event":
            print(event.item.type)
        
        print("=" * 20)

# 실행
asyncio.run(main())