import datetime, json
from discord import Client

def readFile(fileName: str):
    fileObj = open(fileName, "r")  # opens the file in read mode
    words = fileObj.read().splitlines()  # puts the file into a list
    fileObj.close()
    return words

def jsonRead(name: str):
    with open(name) as json_file:
        print("Reading JSON file")
        data = json.load(json_file)
    return data

def log(data: str):
  with open("log.txt", "a") as f:
    f.write(data + "\n")

def get_user_and_date_from_string(dict: dict):
  new_dict = {}
  for user_id, date in dict.items():
    user = Client.get_user(int(user_id))
    if user is None:
      continue
    dates = date.split("-")
    if len(dates) != 3:
      e = ValueError("Hatalı tarih formatı, lütfen düzeltin!")
      print(e)
      continue
    date_obj = datetime(int(dates[0]), int(dates[1]), int(dates[2]))
    print(f"{user} : {date_obj}")
    if date_obj is None:
      continue
    new_dict[user] = date_obj

  return new_dict