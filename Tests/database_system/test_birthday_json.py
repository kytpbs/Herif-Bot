import asyncio
import os
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import Constants
from src import Read
from src.data.birthdays import BirthdayAlreadyExists, BirthdayDoesNotExist
from src.data.providers.birthday_json import BirthdayJson


@pytest.fixture(scope="function", autouse=True)
def json_folder_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "jsons"
    folder.mkdir()
    json_dir = str(folder) + os.sep
    monkeypatch.setattr(Constants, "JSON_FOLDER", json_dir)
    monkeypatch.setattr(Read, "JSON_FOLDER", json_dir)
    return folder


async def test_get_all_birthdays():
    birthdays = BirthdayJson()

    await birthdays.add_birthday(1, 1, date(2023, 1, 1))
    await birthdays.add_birthday(2, 1, date(2023, 1, 2))

    # Make sure today is at UTC since its also checked for UTC in DB
    today = datetime.now(UTC).date()
    birthday = date(2000, today.month, today.day)

    await birthdays.add_birthday(3, 1, birthday)

    assert len(await birthdays.get_birthdays(1)) == 3
    assert len(await birthdays.get_birthdays_today(1)) == 1

    assert await birthdays.get_birthday(1, 1) == date(2023, 1, 1)

    await birthdays.remove_birthday(3, 1)

    await asyncio.sleep(0.1)  # Ensure cache is not used

    assert await birthdays.get_birthday(3, 1) is None
    assert len(await birthdays.get_birthdays_today(1)) == 0


async def test_birthday_exceptions():
    # Clean up before test

    birthdays = BirthdayJson()

    # Test adding duplicate birthday raises exception
    await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-01"))

    with pytest.raises(BirthdayAlreadyExists):
        await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-02"))

    # Test removing non-existent birthday raises exception
    with pytest.raises(BirthdayDoesNotExist):
        await birthdays.remove_birthday(999, 1)
