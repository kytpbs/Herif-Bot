import functools
from typing import Callable, Coroutine

from discord import Client, Message


MessageChecker = Callable[[Message], bool]
AsyncMessageFunction = Callable[[Client, Message], Coroutine]
MessageProcessor = tuple[MessageChecker, AsyncMessageFunction]

functionRegistry: set[MessageProcessor] = set()

async def call_command(message: Message, client: Client):
    for does_message_match_criteria, command in functionRegistry:
        if does_message_match_criteria(message):
            await command(client, message)

def _actually_register_function(func: Callable, response_of: MessageChecker):
    functionRegistry.add((response_of, func))

def register_function(func: Callable, response_of: MessageChecker | str):
    if isinstance(response_of, str):
        def is_equal(message: Message) -> bool:
            return message.content == response_of
        _actually_register_function(func, is_equal)
        return
    _actually_register_function(func, response_of)


def message_command(response_of: str | MessageChecker) -> Callable:
    return functools.partial(register_function, response_of=response_of)
