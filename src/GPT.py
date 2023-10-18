import logging
import os
import discord

import openai
from dotenv import load_dotenv

from Constants import BOT_NAME, SERVER_NAME

load_dotenv()

ERROR = -1
ERROR2 = "ERROR: GPT-3 API Error"
openai.api_key = os.getenv("OPEN_AI_KEY")
if openai.api_key is None:
    logging.critical("OPEN_AI_KEY is not set in .env file")


# noinspection PyBroadException
def question(message: str, user_name: str = "MISSING", server_name: str = SERVER_NAME):
    logging.debug(f"new question: {message} to {BOT_NAME} in {server_name}")
    messages = [
        {
        "role": "system",
        "content": f"You are a discord bot named '{BOT_NAME}' in a discord server named '{server_name}'",
        },
        {
        "role": "user",
        "content": message,
        },
    ]
    if user_name != "MISSING":
        messages[1]['name'] = user_name
    try:
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=500,
        )
    except Exception:
        return ERROR
    if not isinstance(response, dict):
        return ERROR
    answer = response['choices'][0]['message']['content']
    tokens = response['usage']['total_tokens']
    logging.debug(f"{tokens} tokens used")
    return answer

def chat(main_message: str, message_history: dict[discord.User, str]):
    messages = [
        {
        "role": "system",
        "content": f"You are a discord bot named '{BOT_NAME}' in a discord server named {SERVER_NAME}",
        },
    ]
    for user, message in message_history.items():
        messages.append({
        "role": "assistant" if user.bot else "user",
        "name": user.name,
        "content": message,
        })
    
    messages.append({
        "role": "user",
        "content": main_message,
        })
    try:
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=400,
        )
    except openai.OpenAIError:
        return ERROR2
    if not isinstance(response, dict):
        return ERROR2
    answer = response['choices'][0]['message']['content']
    logging.debug("replying to DM, %d tokens used", response['usage']['total_tokens'])
    return answer
