from Commands import setup_commands
from client import get_client_instance
from token_system import get_token

token = get_token()
client = get_client_instance()

setup_commands()

client.run(token)
