import logging
import os
import sys

from dotenv import load_dotenv

from src.logging_system import is_server

loaded = load_dotenv()
token = os.getenv("TOKEN")
dev_token = os.getenv("DEV_TOKEN")


def get_main_token() -> str:
  if token is not None:
    return token  # os.getenv("TOKEN")
  try:
    #  it might not exist that's why we use try catch
    from Token import TOKEN  # type: ignore
    return TOKEN
  except ImportError or ModuleNotFoundError:
    logging.critical("No token found", stack_info=True)
    raise ValueError("No token found")


def get_dev_token() -> str:
  if dev_token is not None:
    return dev_token  # os.getenv("DEV_TOKEN")
  try:
    #  it might not exist that's why we use try catch
    from Token import DEV_TOKEN  # type: ignore
    return DEV_TOKEN
  except ImportError or ModuleNotFoundError:
    logging.critical("No dev token found", stack_info=True)
    return input("Enter your dev token: ")


def get_token() -> str:
  """
  Returns the token to use.
  If the bot is running on the server, it will use the main token.
  If the bot is running on a local machine, it will ask the user if they want to use the dev token.
  If there are any args when starting main, It will use that instead (main/dev)
  """
  if is_server():
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
      return get_dev_token()
    return get_main_token()

  if len(sys.argv) > 1:
    if sys.argv[1] == "dev":
      return get_dev_token()
    elif sys.argv[1] == "main":
      return get_main_token()
    else:
      logging.error("Unknown arg, please use main or dev")

  take = input("Do you want to use the dev token? (y/n): ")

  if take.lower() == "n":
    return get_main_token()
  else:
    return get_dev_token()


if __name__ == "__main__":
  print("args: ", sys.argv)
  print(get_token())
