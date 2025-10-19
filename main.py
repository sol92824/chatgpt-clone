import dotenv
import asyncio

dotenv.load_dotenv()

from agents import Agent, Runner, function_tool, ItemHelpers

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

    message = ""
    args = ""

    # event.type
    # agent_updated_stream_event - agent 상태(state)나 속성(property)이 업데이트될 때 발생
    # run_item_stream_event - agent 업무 처리시 발생
    async for event in stream.stream_events():
        
        if event.type == "raw_response_event":
            event_type = event.data.type

            # agent 응답 중 텍스트로 출력되는 내용 일부를 리턴할 때 (일정 조각 단위로 리턴)
            if event_type == "response.output_text.delta":
                message += event.data.delta
                print(message)
            # agent에서 함수 호출시 전달하는 인자 일부를 리턴할 때 (일정 조각 단위로 리턴)
            elif event_type == "response.function_call_arguments.delta":
                args += event.data.delta
                print(args)
            # agent가 응답 생성을 완전히 마쳤을 때
            elif event_type == "response.completed":
                message = ""
                args = ""

# 실행
asyncio.run(main())