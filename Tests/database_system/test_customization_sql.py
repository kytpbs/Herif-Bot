# pylint: disable=redefined-outer-name
import asyncio
from sys import platform
from typing import AsyncGenerator
from psycopg import sql

import pytest

from src.sql.postgres import PostgresDBClient
from src.data.customizations import (
    CustomCommand,
    CustomizationAlreadyExists,
    CustomizationDoesNotExist,
)
from src.data.providers.customization_sql import CustomizationSQL


@pytest.fixture(scope="session")
def event_loop_policy(request: pytest.FixtureRequest):
    del request  # Unused parameter, but required by pytest fixture signature
    if platform == "win32":
        # psycopg3 does not support the default event loop policy on Windows
        # So when using windows we have to use the WindowsSelectorEventLoopPolicy
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def customizations(
    client: PostgresDBClient,
) -> AsyncGenerator[CustomizationSQL, None]:
    customizations_client = await CustomizationSQL.create(client)
    yield customizations_client
    await client.post(
        sql.SQL("DROP TABLE IF EXISTS {table_name}").format(
            table_name=sql.Identifier(customizations_client._table_name)  # pyright: ignore[reportPrivateUsage] # pylint: disable=protected-access
        )
    )
    client.clear_cache()


async def test_custom_command_crud(
    client: PostgresDBClient, customizations: CustomizationSQL
):
    guild_id = 0
    command_input = "pytest_custom_command"
    response = "pytest response"

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
    client.clear_cache()

    assert await customizations.get_response(guild_id, command_input) is None
    assert await customizations.get_all_custom_commands(guild_id) == {}

    with pytest.raises(CustomizationDoesNotExist):
        await customizations.delete_custom_command(guild_id, command_input)


async def test_duplicate_custom_command_addition(customizations: CustomizationSQL):  # pylint: disable=redefined-outer-name
    guild_id = 0
    command_input = "pytest_duplicate_command"
    response = "first response"
    command = CustomCommand(guild_id, command_input, response)

    await customizations.create_custom_command(guild_id, command_input, response)
    # Second insert should raise exception
    with pytest.raises(CustomizationAlreadyExists):
        await customizations.create_custom_command(guild_id, command_input, "new value")

    commands = await customizations.get_all_custom_commands(guild_id)
    assert commands == {command_input: command}
    await customizations.delete_custom_command(guild_id, command_input)


async def test_delete_non_existent_custom_command(customizations: CustomizationSQL):  # pylint: disable=redefined-outer-name
    with pytest.raises(CustomizationDoesNotExist):
        await customizations.delete_custom_command(0, "does_not_exist")
