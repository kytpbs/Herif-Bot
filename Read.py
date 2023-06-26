from Server_Check import is_server
import json, logging, google.cloud.logging


if is_server():
  logging.basicConfig(level=logging.INFO)
  google_client = google.cloud.logging.Client()
  google_client.setup_logging()
  logger = google_client.logger('discord')
else:
  logging.basicConfig(filename='log.txt', level=logging.INFO)
  logger = logging.getLogger('discord_bot')

def jsonRead(name: str) -> dict:
    with open(name) as json_file:
        print(f"Reading {name}")
        data = json.load(json_file)
    return data

def log(name: str) -> None:
  if isinstance(logger, google.cloud.logging.Logger):
    logger.log(name)
  else:
    logger.info(name)

if __name__ == "__main__":
  print(RuntimeWarning("This file is not meant to be run directly!"))
  print("1. jsonRead")
  print("2. exit")
  inp = input(">>> ")
  if inp == "1":
    print("Enter file name: ")
    file_name = input(">>> ")
    print(jsonRead(file_name))
  elif inp == "2":
    exit()    
