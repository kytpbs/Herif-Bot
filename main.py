# import token_system first so that logging is setup correctly (ie. cloud logging) before everything else runs
from src.token_system import get_token
from src.client import get_client_instance

token = get_token()
client = get_client_instance()


client.run(token)
