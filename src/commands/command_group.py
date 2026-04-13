from abc import ABC, abstractmethod
from typing import Any
import logging

import discord

LOGGER = logging.getLogger("commands")

CommandList = list[
    discord.app_commands.Command[Any, ..., Any]
    | discord.app_commands.Group
    | discord.app_commands.ContextMenu
]


class CommandGroup(ABC):
    @classmethod
    def register_commands(cls, tree: discord.app_commands.CommandTree) -> None:
        """Register commands to the given command tree. Uses the default implementation.
        If you have subcommands or similar, you should override this method.

        Args:
            tree (discord.app_commands.CommandTree): The command tree to register commands to.
        """
        for command in cls.get_commands():
            tree.add_command(command)
            LOGGER.debug("Registered command: %s", command.name)

    @classmethod
    @abstractmethod
    def get_commands(
        cls,
    ) -> CommandList:
        """Get the list of commands that may be wished to be registered in this command group.
        Returns:
            CommandList: The list of commands.
        """
