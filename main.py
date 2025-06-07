# import token_system first so that logging is setup correctly (ie. cloud logging) before everything else runs
# Ensure logging is set up before any other imports
from src.logging_system import setup_logging
setup_logging()

# ruff: noqa: E402
# pylint: disable=wrong-import-position
from src.token_system import get_token
from src.client import get_client_instance
from src.commands import setup_commands

token = get_token()
client = get_client_instance()

setup_commands()

client.run(token)
