import asyncio
import random
import ssl
import json
import time
import uuid
import requests
import shutil
from colorama import Fore, Style
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from dataclasses import dataclass
from typing import Dict

# Konfigurasi logger
logger.remove()  # Menghapus handler default
logger.add(
    lambda msg: print(msg),
    format="[{time:HH:mm:ss}] {level} | {message}",
    level="INFO",
    colorize=True
)
logger.add(
    lambda msg: print(msg),
    format="[{time:HH:mm:ss}] {level} | {message}",
    level="ERROR",
    colorize=True
)
logger.add(
    lambda msg: print(msg),
    format="[{time:HH:mm:ss}] {level} | {message}",
    level="DEBUG",
    colorize=True
)

@dataclass
class Configuration:
    websocket_host: str = "proxy2.wynd.network:4444"
    retry_interval: int = 20000
    
class BotInstance:
    def __init__(self):
        self.total_data_usage: Dict[str, int] = {}
        
    def format_data_usage(self, bytes_count: int) -> str:
        kb = bytes_count / 1024
        if kb >= 1024:
            mb = kb / 1024
            return f"{mb:.2f} MB"
        return f"{kb:.2f} KB"

async def connect_to_wss(socks5_proxy, user_id):
    bot = BotInstance()
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"{Fore.LIGHTWHITE_EX}{device_id}{Style.RESET_ALL}")
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/","wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy2.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"{Fore.LIGHTBLUE_EX}{send_message}{Style.RESET_ALL}")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    # Menghitung penggunaan data
                    data_usage = len(response)
                    if user_id not in bot.total_data_usage:
                        bot.total_data_usage[user_id] = 0
                    bot.total_data_usage[user_id] += data_usage
                    
                    message = json.loads(response)
                    logger.info(f"{Fore.LIGHTBLUE_EX}{message}{Style.RESET_ALL}")
                    
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",
                                "version": "4.29.0",
                            }
                        }
                        logger.debug(f"{Fore.LIGHTWHITE_EX}{auth_response}{Style.RESET_ALL}")
                        logger.info(f"{Fore.LIGHTCYAN_EX}Mencoba autentikasi untuk userID: {user_id}{Style.RESET_ALL}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        formatted_usage = bot.format_data_usage(bot.total_data_usage[user_id])
                        logger.info(f"{Fore.LIGHTGREEN_EX}Menerima PONG untuk UserID: {Fore.LIGHTMAGENTA_EX}{user_id}, {Fore.LIGHTGREEN_EX}Total penggunaan data: {Fore.LIGHTYELLOW_EX}{formatted_usage}{Style.RESET_ALL}")
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(f"{Fore.LIGHTRED_EX}Error untuk proxy {socks5_proxy}: {str(e)}{Style.RESET_ALL}")
            await asyncio.sleep(20)  # retry interval

async def main():
    #find user_id on the site in conlose localStorage.getItem('userId') (if you can't get it, write allow pasting)
    _user_id = '2ob7GOuG5onrzrLRBmsjv821Q4o'
    with open('local_proxies.txt', 'r') as file:
            local_proxies = file.read().splitlines()
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in local_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    #letsgo
    try: 
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error(f"{Fore.LIGHTRED_EX}Ctrl + C is pressed..., Stoping Program{Style.RESET_ALL}")
