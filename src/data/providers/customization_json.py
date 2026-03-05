from collections.abc import Mapping, MutableMapping
from typing import Final

from typing_extensions import override

from src.data.customizations import (
    Command,
    CustomCommand,
    CustomizationAlreadyExists,
    CustomizationDoesNotExist,
    CustomizationProvider,
    GuildID,
    Response,
    UserID,
)
from src.Helpers.helper_functions import DiskDict

GuildCustomizations = MutableMapping[str, MutableMapping[Command, CustomCommand]]


class CustomizationJson(CustomizationProvider):
    def __init__(self):
        self._guild_customizations: Final[GuildCustomizations] = DiskDict(
            "customizations.json"
        )

    def _guild_key(self, guild_id: GuildID) -> str:
        return str(guild_id)

    @override
    async def create_custom_command(
        self,
        guild_id: GuildID,
        command_input: Command,
        response: Response,
        added_by_user_id: UserID | None = None,
    ) -> None:
        commands = self._guild_customizations.setdefault(self._guild_key(guild_id), {})
        if command_input in commands:
            raise CustomizationAlreadyExists()
        commands[command_input] = CustomCommand(
            guild_id=guild_id,
            command_input=command_input,
            response=response,
            added_by_user_id=added_by_user_id,
        )

    @override
    async def delete_custom_command(
        self, guild_id: GuildID, command_input: Command
    ) -> None:
        commands = self._guild_customizations.setdefault(self._guild_key(guild_id), {})
        if command_input not in commands:
            raise CustomizationDoesNotExist()
        del commands[command_input]

    @override
    async def get_response(
        self, guild_id: GuildID, command_input: Command
    ) -> CustomCommand | None:
        commands = self._guild_customizations.setdefault(self._guild_key(guild_id), {})
        if command_input not in commands:
            return None
        record = commands[command_input]
        return record

    @override
    async def get_all_custom_commands(
        self, guild_id: GuildID, limit: int | None = None
    ) -> Mapping[Command, CustomCommand]:
        commands = self._guild_customizations.setdefault(self._guild_key(guild_id), {})
        normalized_commands: dict[Command, CustomCommand] = {}

        for index, (cmd, data) in enumerate(commands.items()):
            if limit is not None and index >= limit:
                break
            normalized_commands[cmd] = data

        return normalized_commands

    @override
    async def get_creator(
        self, guild_id: GuildID, command_input: Command
    ) -> UserID | None:
        response = await self.get_response(guild_id, command_input)
        if response is None:
            return None
        return response.added_by_user_id
