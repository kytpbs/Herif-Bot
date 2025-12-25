import asyncio
from sys import platform

import pytest

from src.sql.postgres import PostgresDBClient
from src.data.customizations import CustomizationDoesNotExist
from src.data.providers.customization_sql import CustomizationSQL
from src.sql.database import DatabaseClient


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
        await customizations.create_custom_command(
            guild_id, command_input, response, added_by_user_id=999
        )

        assert await customizations.get_response(guild_id, command_input) == response
        assert await customizations.get_all_custom_commands(guild_id) == {
            command_input: response
        }

        await customizations.delete_custom_command(guild_id, command_input)
        await asyncio.sleep(0.1)  # Ensure cache invalidation

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

    try:
        await customizations.create_custom_command(guild_id, command_input, response)
        # Second insert should be ignored due to ON CONFLICT DO NOTHING
        await customizations.create_custom_command(guild_id, command_input, "new value")

        commands = await customizations.get_all_custom_commands(guild_id)
        assert commands == {command_input: response}
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
