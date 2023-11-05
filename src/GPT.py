import logging
import os
import threading
from queue import LifoQueue
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

async def create_message_history(channel: discord.abc.Messageable, limit:int = 10):
    message_history = []
    async for message in channel.history(limit=limit):
        message_history.append((message.author, message.content))
    return message_history

def modified_create(queue: LifoQueue, *args, **kwargs):
    queue.put(openai.ChatCompletion.create(*args, **kwargs))

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

def chat(main_message: str, message_history: list[tuple[discord.User, str]]):
    messages = [
        {
        "role": "system",
        "content": f"You are a discord bot named '{BOT_NAME}' in a discord server named {SERVER_NAME}",
        },
    ]
    for user, message in message_history:
        if user.bot:
            messages.append({
            "role": "assistant",
            "content": message,
            })
        else:
            messages.append({
            "role": "user",
            "name": user.name,
            "content": message,
            })
    
    messages.append({
        "role": "user",
        "content": main_message,
        })
    try:
        queue = LifoQueue()
        thread = threading.Thread(target=modified_create,
                                        name="chat Request",
                                        args=[queue],
                                        kwargs={'model': "gpt-3.5-turbo",
                                            'messages': messages,
                                            'max_tokens': 400})
        thread.start()
        thread.join(30)
        if thread.is_alive():
            logging.error("thread timed out")
            return ERROR2
        response = queue.get()
    except openai.OpenAIError as error:
        logging.error(error, stack_info=True)
        return ERROR2
    if not isinstance(response, dict):
        logging.error("response is not a dict: %s", response)
        return ERROR2
    answer = response['choices'][0]['message']['content']
    logging.debug("replying to DM, %d tokens used", response['usage']['total_tokens'])
    return answer
