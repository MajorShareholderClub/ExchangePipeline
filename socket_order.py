"""
Socket Test
"""

import asyncio
from pipe.connection import CoinOrderBookWebsocket
from pipe.socket_init import coin_present_websocket


if __name__ == "__main__":
    asyncio.run(coin_present_websocket(CoinOrderBookWebsocket))
