from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias

from src.sql.errors import (
    AlreadyExists,
    NotConnectedError,
    SQLError,
    SQLFailedMiserably,
)


class CustomizationError(SQLError, Exception):
    pass


class DBNotConnected(CustomizationError, NotConnectedError):
    pass


class CustomizationAlreadyExists(AlreadyExists, CustomizationError):
    pass


class CustomizationDoesNotExist(CustomizationError):
    pass


class CustomizationUnknownError(CustomizationError, SQLFailedMiserably):
    pass


UserID: TypeAlias = int
GuildID: TypeAlias = int
Command: TypeAlias = str
Response: TypeAlias = str

@dataclass
class CustomCommand:
    guild_id: GuildID
    command_input: Command
    response: Response
    added_by_user_id: UserID | None = None

    def __str__(self) -> str:
        return self.response


class CustomizationProvider(ABC):
    @abstractmethod
    async def create_custom_command(
        self,
        guild_id: GuildID,
        command_input: Command,
        response: Response,
        added_by_user_id: UserID | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete_custom_command(
        self, guild_id: GuildID, command_input: Command
    ) -> None:
        pass

    @abstractmethod
    async def get_response(self, guild_id: GuildID, command_input: Command) -> CustomCommand | None:
        pass

    @abstractmethod
    async def get_all_custom_commands(self, guild_id: GuildID, limit: int | None = None) -> Mapping[Command, CustomCommand]:
        pass

    @abstractmethod
    async def get_creator(self, guild_id: GuildID, command_input: Command) -> UserID | None:
        """
        Get the user ID of the user who added the custom command, if available.
        All providers may not support this.
        """
        return None
