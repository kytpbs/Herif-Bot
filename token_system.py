from dotenv import load_dotenv
from logging_system import log, is_server
import logging
import os
import sys

loaded = load_dotenv()

if loaded:  # os.getenv
  token = os.getenv("TOKEN")
  dev_token = os.getenv("DEV_TOKEN")
else:  # set them None
  token = None
  dev_token = None


def get_main_token() -> str:
  if loaded and token is not None:
    return token  # os.getenv("TOKEN")
  try:
    from Token import TOKEN  # type: ignore
    return TOKEN
  except ImportError:
    log("No token found", logging.ERROR)
    return input("Enter your token: ")


def get_dev_token() -> str:
  if loaded and dev_token is not None:
    return dev_token  # os.getenv("DEV_TOKEN")
  try:
    from Token import DEV_TOKEN
    return DEV_TOKEN
  except ImportError:
    log("No dev token found", logging.CRITICAL)
    return input("Enter your dev token: ")


def get_token() -> str:
  """
  Returns the token to use.
  If the bot is running on the server, it will use the main token.
  If the bot is running on a local machine, it will ask the user if they want to use the dev token.
  If there are any args when starting main, It will use that instead (main/dev)
  """
  if is_server():
    if sys.argv[1] == "dev":
      return get_dev_token()
    return get_main_token()

  if len(sys.argv) > 1:
    if sys.argv[1] == "dev":
      return get_dev_token()
    elif sys.argv[1] == "main":
      return get_main_token()

  take = input("Do you want to use the dev token? (y/n): ")

  if take.lower() == "n":
    return get_main_token()
  else:
    return get_dev_token()


if __name__ == "__main__":
  print("args: ", sys.argv)
  print(get_token())
