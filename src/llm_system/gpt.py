import logging
import os
from typing import Optional

import discord
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

from src.llm_system.llm_data import MessageHistory
from src.llm_system.llm_discord_integration import (
    get_message_from_interaction,
    get_message_history_from_discord_channel,
    get_message_history_from_discord_message,
)
from src.llm_system.llm_errors import (
    APICallFailedError,
    NoTokenError,
    RanOutOfMoneyError,
    TooFastError,
)
from src.llm_system.openai_fixer import GPTMessages

SYSTEM_PROMPT_BASE = (
    "You are a discord bot named '{bot_name}' in a discord {server_name}"
)

load_dotenv()

API_KEY = os.getenv("OPEN_AI_KEY")
LOGGER = logging.getLogger("GPT")
client: Optional[OpenAI] = OpenAI(api_key=API_KEY) if API_KEY else None

if API_KEY is None:
    logging.critical("OPEN_AI_KEY is not set in .env file, GPT will not work")


async def chat(message_history: GPTMessages) -> str:
    if client is None:
        raise NoTokenError()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=message_history.to_gpt_list(),
        )
    except RateLimitError as e:
        LOGGER.error(f"Rate limit error {e}")
        if e.code == 'insufficient_quota':
            raise RanOutOfMoneyError() from e
        raise TooFastError("Rate limit hit") from e

    except Exception as e:
        LOGGER.error(f"Failed to complete message history {e}")
        raise APICallFailedError("Something went wrong with the API call") from e

    choices = response.choices
    if not choices:
        raise APICallFailedError("No response from the API")

    response = choices[0].message.content

    if not response:
        raise APICallFailedError("No response from the API results content")

    return response


async def message_chat(message: discord.Message) -> str:
    """_summary_

    Args:
        message (discord.Message): _description_

    Returns:
        str: _description_
    """
    server_name = ("server named: " + message.guild.name) if message.guild else "DM"
    # You will not like this, but it's the only way to get the bot name from the message, at least that I can think of
    # we will always be logged in when this function is called, so we can safely get the name
    bot_name = message.channel._state._get_client().user.name  # pylint: disable=protected-access # type: ignore

    system_prompt = SYSTEM_PROMPT_BASE.format(
        bot_name=bot_name, server_name=server_name
    )

    message_history = await get_message_history_from_discord_message(message)

    message_history = GPTMessages.from_message_history(message_history, system_prompt)

    return await chat(message_history)


async def interaction_chat(
    interaction: discord.Interaction, message: str, include_history: bool = True
) -> str:
    bot_name = interaction.client.user.name  # type: ignore # we will always be logged in when this function is called
    server_name = (
        ("server named: " + interaction.guild.name) if interaction.guild else "DM"
    )

    system_prompt = SYSTEM_PROMPT_BASE.format(
        bot_name=bot_name, server_name=server_name
    )

    if include_history and isinstance(interaction.channel, discord.abc.Messageable):
        message_history = await get_message_history_from_discord_channel(
            interaction.channel, limit=10 if include_history else 0
        )
    else:
        message_history = MessageHistory()

    message_history = GPTMessages.from_message_history(
        message_history,
        system_prompt,
        main_message=get_message_from_interaction(interaction, message),
    )

    return await chat(message_history)
