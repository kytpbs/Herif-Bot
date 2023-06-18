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

if __name__ == "__main__":
  print(RuntimeWarning("This file is not meant to be run directly!"))
  print("1. readFile")
  print("2. jsonRead")
  print("3. log")
  print("4. exit")
  inp = input(">>> ")
  if inp == "1":
    print("Enter file name: ")
    file_name = input(">>> ")
    print(readFile(file_name))
  elif inp == "2":
    print("Enter file name: ")
    file_name = input(">>> ")
    print(jsonRead(file_name))
  elif inp == "3":
    print("Enter data: ")
    data = input(">>> ")
    log(data)
  elif inp == "4":
    exit()
  