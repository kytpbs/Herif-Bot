import logging
import os

import openai
from dotenv import load_dotenv

from Constants import BOT_NAME, SERVER_NAME

load_dotenv()

ERROR = -1
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


# noinspection PyBroadException
def chat(message_response_dict: dict[str, str], new_message: str = "MISSING",
         user_name: str = "MISSING", dont_send_token_usage: bool = True):
  """
  message_response_dict: left is the message, right is the response from the bot
  """
  logging.debug(f"new chat: {message_response_dict}")
  messages = [
    {
      "role": "system",
      "content": "You are a discord bot named 'Cupids' in a discord server named Cupids",
    },
  ]
  
  if user_name != "MISSING":
    messages.append({
      "role": "system",
      "content": f"You Are Talking With {user_name}",
    })
  
  for message, response in message_response_dict.items():
    messages.append({
      "role": "user",
      "content": message,
    })
    messages.append({
      "role": "assistant",
      "content": response,
    })

  if new_message != "MISSING":
    messages.append({
      "role": "user",
      "content": new_message,
    })
  try:
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=messages,
    )
  except Exception:
    return ERROR
  if not isinstance(response, dict):
    return ERROR
  tokens = response['usage']['total_tokens']
  logging.debug(f"{tokens} tokens used")
  answer = response['choices'][0]['message']
  if not dont_send_token_usage:
    return answer
  return answer
