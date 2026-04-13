# pylint: disable=redefined-outer-name
import os
from pathlib import Path

import pytest

import Constants
from src import Read
from src.data.server_config import (
    BirthdayConfig,
    CustomizationConfig,
    ServerConfigDoesNotExist,
)
from src.data.providers.server_config_json import ServerConfigJson


@pytest.fixture(scope="function", autouse=True)
def json_folder_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "jsons"
    folder.mkdir()
    json_dir = str(folder) + os.sep
    monkeypatch.setattr(Constants, "JSON_FOLDER", json_dir)
    monkeypatch.setattr(Read, "JSON_FOLDER", json_dir)
    return folder


@pytest.fixture(scope="function")
def server_configs() -> ServerConfigJson:
    return ServerConfigJson()


async def test_birthday_config_crud(server_configs: ServerConfigJson):
    guild_id = 123456
    config = BirthdayConfig(channel_id=999, role_id=888)

    # Test set and get
    await server_configs.set_birthday_config(guild_id, config)
    fetched = await server_configs.get_birthday_config(guild_id)
    assert fetched is not None
    assert fetched.channel_id == 999
    assert fetched.role_id == 888

    # Test get non-existent
    assert await server_configs.get_birthday_config(999999) is None

    # Test remove
    await server_configs.remove_birthday_config(guild_id)
    assert await server_configs.get_birthday_config(guild_id) is None


async def test_birthday_config_overwrite(server_configs: ServerConfigJson):
    guild_id = 123456
    config1 = BirthdayConfig(channel_id=111, role_id=222)
    config2 = BirthdayConfig(channel_id=333, role_id=444)

    await server_configs.set_birthday_config(guild_id, config1)
    await server_configs.set_birthday_config(guild_id, config2)

    fetched = await server_configs.get_birthday_config(guild_id)
    assert fetched is not None
    assert fetched.channel_id == 333
    assert fetched.role_id == 444


async def test_birthday_config_without_role(server_configs: ServerConfigJson):
    guild_id = 123456
    config = BirthdayConfig(channel_id=999, role_id=None)

    await server_configs.set_birthday_config(guild_id, config)
    fetched = await server_configs.get_birthday_config(guild_id)
    assert fetched is not None
    assert fetched.channel_id == 999
    assert fetched.role_id is None


async def test_remove_nonexistent_birthday_config(server_configs: ServerConfigJson):
    with pytest.raises(ServerConfigDoesNotExist):
        await server_configs.remove_birthday_config(999999)


async def test_customization_config_crud(server_configs: ServerConfigJson):
    guild_id = 123456
    config = CustomizationConfig(is_enabled=False)

    # Test set and get
    await server_configs.set_customization_config(guild_id, config)
    fetched = await server_configs.get_customization_config(guild_id)
    assert fetched.is_enabled is False

    # Test get non-existent returns default (enabled=True)
    default = await server_configs.get_customization_config(999999)
    assert default.is_enabled is True

    # Test remove
    await server_configs.remove_customization_config(guild_id)
    fetched_after_remove = await server_configs.get_customization_config(guild_id)
    assert fetched_after_remove.is_enabled is True


async def test_customization_config_default_values(server_configs: ServerConfigJson):
    # When not set, should return default (enabled=True)
    fetched = await server_configs.get_customization_config(999999)
    assert fetched.is_enabled is True


async def test_customization_config_toggle(server_configs: ServerConfigJson):
    guild_id = 123456

    # Enable
    await server_configs.set_customization_config(
        guild_id, CustomizationConfig(is_enabled=True)
    )
    assert (await server_configs.get_customization_config(guild_id)).is_enabled is True

    # Disable
    await server_configs.set_customization_config(
        guild_id, CustomizationConfig(is_enabled=False)
    )
    assert (await server_configs.get_customization_config(guild_id)).is_enabled is False

    # Re-enable
    await server_configs.set_customization_config(
        guild_id, CustomizationConfig(is_enabled=True)
    )
    assert (await server_configs.get_customization_config(guild_id)).is_enabled is True


async def test_remove_nonexistent_customization_config(
    server_configs: ServerConfigJson,
):
    with pytest.raises(ServerConfigDoesNotExist):
        await server_configs.remove_customization_config(999999)


async def test_config_accessor_lazy_loading(server_configs: ServerConfigJson):
    guild_id = 123456
    birthday_cfg = BirthdayConfig(channel_id=111, role_id=222)
    customization_cfg = CustomizationConfig(is_enabled=False)

    await server_configs.set_birthday_config(guild_id, birthday_cfg)
    await server_configs.set_customization_config(guild_id, customization_cfg)

    # Get the accessor
    accessor = server_configs.get_config(guild_id)

    # Access birthday config
    fetched_birthday = await accessor.birthday_config
    assert fetched_birthday is not None
    assert fetched_birthday.channel_id == 111
    assert fetched_birthday.role_id == 222

    # Access customization config
    fetched_customization = await accessor.customization_config
    assert fetched_customization.is_enabled is False


async def test_config_accessor_caching(
    server_configs: ServerConfigJson, monkeypatch: pytest.MonkeyPatch
):
    """Test that the accessor caches results using monkey-patching"""
    guild_id = 123456
    birthday_cfg = BirthdayConfig(channel_id=111, role_id=222)

    await server_configs.set_birthday_config(guild_id, birthday_cfg)

    # Get the accessor
    accessor = server_configs.get_config(guild_id)

    # Patch the provider's get_birthday_config method to track calls
    original_method = server_configs.get_birthday_config
    call_count = 0

    async def tracked_get_birthday_config(guild_id: int) -> BirthdayConfig | None:
        nonlocal call_count
        call_count += 1
        return await original_method(guild_id)

    monkeypatch.setattr(
        server_configs, "get_birthday_config", tracked_get_birthday_config
    )

    # First access - should call the method
    result1 = await accessor.birthday_config
    assert result1 is not None
    assert call_count == 1

    # Second access - should use cache (within TTL)
    result2 = await accessor.birthday_config
    assert result2 is not None
    # Due to alru_cache, the call count should still be 1
    assert call_count == 1

    # Results should be the same
    assert result1.channel_id == result2.channel_id
    assert result1.role_id == result2.role_id


async def test_multiple_guilds_isolation(server_configs: ServerConfigJson):
    guild1 = 111
    guild2 = 222

    config1 = BirthdayConfig(channel_id=1001, role_id=1002)
    config2 = BirthdayConfig(channel_id=2001, role_id=2002)

    await server_configs.set_birthday_config(guild1, config1)
    await server_configs.set_birthday_config(guild2, config2)

    fetched1 = await server_configs.get_birthday_config(guild1)
    fetched2 = await server_configs.get_birthday_config(guild2)

    assert fetched1 is not None
    assert fetched1.channel_id == 1001
    assert fetched2 is not None
    assert fetched2.channel_id == 2001
