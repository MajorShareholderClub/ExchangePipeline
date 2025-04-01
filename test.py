import asyncio
import json
import websockets
from common.setting.parameter.connection_parameter import bithumb_config
from typing import Any


async def connect_websocket(config: dict[str, Any]) -> None:
    """
    웹소켓에 연결하고 데이터를 수신합니다.

    Args:
        config (dict[str, Any]): 연결 설정 (함수 combine_url_and_parameters의 반환값)
    """
    url: str = config["url"]
    socket_parameters: dict | list = config["parameters"]
    timeout: int = config["timeout"]

    if not socket_parameters:
        return

    async with websockets.connect(
        url,
        ping_interval=30,
        ping_timeout=60,
    ) as websocket:
        # 파라미터 전송
        param_json: str = json.dumps(socket_parameters)
        await websocket.send(param_json)

        # 메시지 수신
        while True:
            message: str = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            print(message)


async def test_socket():
    """
    소켓 연결 테스트를 실행합니다.
    """
    # 업비트 BTC 티커 연결 설정
    config = bithumb_config.build()
    print(config)
    # 웹소켓 연결
    await connect_websocket(config)


if __name__ == "__main__":
    # 소켓 연결 테스트 실행
    asyncio.run(test_socket())
