# import token_system first so that logging is setup correctly (ie. cloud logging) before everything else runs
from src.token_system import get_token
from sys import platform
from src.client import get_client_instance

token = get_token()
client = get_client_instance()


# Psycopg3 is not compatible with asyncio on Windows's default event loop: "ProactorEventLoop"
if platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

client.run(token)
