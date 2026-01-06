import asyncio
from sys import platform

import pytest

from src.sql.postgres import PostgresDBClient
from src.data.customizations import CustomCommand, CustomizationAlreadyExists, CustomizationDoesNotExist
from src.data.providers.customization_sql import CustomizationSQL


@pytest.fixture(scope="module")
def event_loop_policy(request: pytest.FixtureRequest):
    del request  # Unused parameter, but required by pytest fixture signature
    if platform == "win32":
        # psycopg3 does not support the default event loop policy on Windows
        # So when using windows we have to use the WindowsSelectorEventLoopPolicy
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


async def test_custom_command_crud():
    client = PostgresDBClient()
    customizations = await CustomizationSQL.create(client)

    guild_id = 0
    command_input = "pytest_custom_command"
    response = "pytest response"

    try:
        command = CustomCommand(guild_id, command_input, response, added_by_user_id=999)
        await customizations.create_custom_command(
            command.guild_id,
            command.command_input,
            command.response,
            added_by_user_id=command.added_by_user_id,
        )

        assert await customizations.get_response(guild_id, command_input) == command
        assert await customizations.get_all_custom_commands(guild_id) == {
            command_input: command
        }

        await customizations.delete_custom_command(guild_id, command_input)
        await asyncio.sleep(0.5)  # Ensure cache invalidation

        assert await customizations.get_response(guild_id, command_input) is None
        assert await customizations.get_all_custom_commands(guild_id) == {}
    finally:
        try:
            await customizations.delete_custom_command(guild_id, command_input)
        except CustomizationDoesNotExist:
            pass
        await client.close()


async def test_duplicate_custom_command_addition():
    client = PostgresDBClient()
    customizations = await CustomizationSQL.create(client)

    guild_id = 0
    command_input = "pytest_duplicate_command"
    response = "first response"
    command = CustomCommand(guild_id, command_input, response)

    try:
        await customizations.create_custom_command(guild_id, command_input, response)
        # Second insert should raise exception
        with pytest.raises(CustomizationAlreadyExists):
            await customizations.create_custom_command(guild_id, command_input, "new value")

        commands = await customizations.get_all_custom_commands(guild_id)
        assert commands == {command_input: command}
    finally:
        try:
            await customizations.delete_custom_command(guild_id, command_input)
        except CustomizationDoesNotExist:
            pass
        await client.close()


async def test_delete_non_existent_custom_command():
    client = PostgresDBClient()
    customizations = await CustomizationSQL.create(client)

    with pytest.raises(CustomizationDoesNotExist):
        await customizations.delete_custom_command(0, "does_not_exist")

    await client.close()
