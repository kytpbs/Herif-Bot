import os
from pathlib import Path

import pytest

import Constants
from src import Read
from src.data.customizations import (
    CustomizationAlreadyExists,
    CustomizationDoesNotExist,
)
from src.data.providers.customization_json import CustomizationJson


@pytest.fixture()
def json_folder_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "jsons"
    folder.mkdir()
    json_dir = str(folder) + os.sep
    monkeypatch.setattr(Constants, "JSON_FOLDER", json_dir)
    monkeypatch.setattr(Read, "JSON_FOLDER", json_dir)
    return folder


async def test_custom_command_crud_json(json_folder_fixture: Path):
    del json_folder_fixture  # ensures fixture is used to isolate files
    customizations = CustomizationJson()

    guild_id = 0
    command_input = "pytest_custom_command"
    response = "pytest response"

    await customizations.create_custom_command(
        guild_id, command_input, response, added_by_user_id=999
    )

    fetched = await customizations.get_response(guild_id, command_input)
    assert fetched is not None
    assert fetched.response == response
    assert fetched.added_by_user_id == 999

    commands = await customizations.get_all_custom_commands(guild_id)
    assert command_input in commands
    assert commands[command_input].response == response

    await customizations.delete_custom_command(guild_id, command_input)

    assert await customizations.get_response(guild_id, command_input) is None
    assert await customizations.get_all_custom_commands(guild_id) == {}


async def test_duplicate_custom_command_addition_json(json_folder_fixture: Path):
    del json_folder_fixture  # ensures fixture is used to isolate files
    customizations = CustomizationJson()

    guild_id = 0
    command_input = "pytest_duplicate_command"
    response = "first response"

    await customizations.create_custom_command(guild_id, command_input, response)

    with pytest.raises(CustomizationAlreadyExists):
        await customizations.create_custom_command(guild_id, command_input, "new value")

    commands = await customizations.get_all_custom_commands(guild_id)
    assert command_input in commands
    assert commands[command_input].response == response


async def test_delete_non_existent_custom_command_json(json_folder_fixture: Path):
    del json_folder_fixture
    customizations = CustomizationJson()

    with pytest.raises(CustomizationDoesNotExist):
        await customizations.delete_custom_command(0, "does_not_exist")
