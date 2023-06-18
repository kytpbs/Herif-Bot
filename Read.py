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