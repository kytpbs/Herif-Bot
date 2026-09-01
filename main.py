# Ensure logging is set up before any other imports
# This ensures that errors occurring during the import of other modules are logged
from src.logging_system import setup_logging

setup_logging()

# ruff: noqa: E402
# pylint: disable=wrong-import-position
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
