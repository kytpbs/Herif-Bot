# import token_system first so that logging is setup correctly (ie. cloud logging) before everything else runs
from src.token_system import get_token
from src.client import get_client_instance
from command_controller import setup_commands

token = get_token()
client = get_client_instance()

setup_commands()

client.run(token)
