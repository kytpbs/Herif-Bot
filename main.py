from src.client import get_client_instance
from src.commands import setup_commands
from src.token_system import get_token

token = get_token()
client = get_client_instance()

setup_commands()

client.run(token)
