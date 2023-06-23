import json

def jsonRead(name: str) -> dict:
    with open(name) as json_file:
        print(f"Reading {name}")
        data = json.load(json_file)
    return data

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
  