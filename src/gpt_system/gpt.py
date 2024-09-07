import logging
import os
from typing import Optional

import discord
from dotenv import load_dotenv
from openai import OpenAI

from Constants import BOT_NAME, SERVER_NAME
from src.gpt_system.gpt_data import GPTMessages
from src.gpt_system.gpt_discord_integration import (
    get_message_history_from_discord_message,
)
from src.gpt_system.gpt_errors import APICallFailedError, NoTokenError

SYSTEM_PROMPT = (
    f"You are a discord bot named '{BOT_NAME}' in a discord server named {SERVER_NAME}"
)

load_dotenv()

API_KEY = os.getenv("OPEN_AI_KEY")
LOGGER = logging.getLogger("GPT")
client: Optional[OpenAI] = OpenAI(api_key=API_KEY) if API_KEY else None

if API_KEY is None:
    logging.critical("OPEN_AI_KEY is not set in .env file, GPT will not work")


async def chat(message: discord.Message) -> str:
    """_summary_

    Args:
        message (discord.Message): _description_

    Returns:
        str: _description_

    Raises:
        NoTokenError: _description_
        APICallFailedError: _description_
        RanOutOfMoneyError: _description_
    """

    if client is None:
        raise NoTokenError()

    message_history = await get_message_history_from_discord_message(message)

    message_history = GPTMessages.convert_and_merge(message_history, SYSTEM_PROMPT)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message_history.to_gpt_list(),  # type: ignore # its all correct, don't worry
        )
    except Exception as e:
        LOGGER.error(f"Failed to complete message history {e}")
        raise APICallFailedError("Something went wrong with the API call") from e

    choices = response.choices
    if not choices:
        raise APICallFailedError("No response from the API")

    response = choices[0].message.content

    if not response:
        raise APICallFailedError("No response from the API")

    return response

async def message_chat(message: discord.Message):
    return await chat(message)
