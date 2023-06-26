from sys import platform

def is_server() -> bool:
    print(f"platform: {platform}")
    return platform == "linux" or platform == "linux2"
    
if __name__ == "__main__":
    print(f"This file is not meant to be run directly!")
    print(is_server())
    data = "This device is "
    if not is_server():
        data += "not "
    data += "a server"
    print(data)