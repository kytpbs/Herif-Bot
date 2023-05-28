import json


def readFile(fileName: str):
    fileObj = open(fileName, "r")  # opens the file in read mode
    words = fileObj.read().splitlines()  # puts the file into an array
    fileObj.close()
    return words

def jsonRead(name: str):
    with open(name) as json_file:
        print("Reading JSON file")
        data = json.load(json_file)
    print(data)
    return data