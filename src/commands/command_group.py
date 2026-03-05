from abc import ABC, abstractmethod
import logging

import discord

LOGGER = logging.getLogger("commands")

class CommandGroup(ABC):
    @classmethod
    def register_commands(cls, tree: discord.app_commands.CommandTree) -> None:
        # Default implementation, Should be overridden if there are subcommands or similar
        for command in cls.get_commands():
            tree.add_command(command)
            LOGGER.debug("Registered command: %s", command.name)

    @classmethod
    @abstractmethod
    def get_commands(cls) -> list[discord.app_commands.Command | discord.app_commands.Group | discord.app_commands.ContextMenu]:
        pass

