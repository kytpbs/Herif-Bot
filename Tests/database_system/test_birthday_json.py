import asyncio
import os
from datetime import UTC, date, datetime
import pytest
from src.data.providers.birthday_json import BirthdayJsonDB
from src.data.birtdays import BirthdayAlreadyExists, BirthdayDoesNotExist


def cleanup_test_files():
    """Clean up JSON files created during testing"""
    jsons_file = "jsons/birthday_guild.json"
    if os.path.exists(jsons_file):
        os.remove(jsons_file)


async def test_get_all_birthdays():
    # Clean up before test
    cleanup_test_files()

    birthdays = BirthdayJsonDB()

    try:
        await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-01"))
        await birthdays.add_birthday(2, 1, date.fromisoformat("2023-01-02"))

        # Make sure today is at UTC since its also checked for UTC in DB
        today = datetime.now(UTC).date()
        birthday = date(2000, today.month, today.day)

        await birthdays.add_birthday(3, 1, birthday)

        assert len(await birthdays.get_all_birthdays(1)) == 3
        assert len(await birthdays.get_birthdays_today(1)) == 1

        assert await birthdays.get_birthday(1, 1) == date.fromisoformat("2023-01-01")

        await birthdays.remove_birthday(3, 1)

        await asyncio.sleep(0.1)  # Ensure cache is not used

        assert await birthdays.get_birthday(3, 1) is None
        assert len(await birthdays.get_birthdays_today(1)) == 0
    finally:
        # Clean up after test
        cleanup_test_files()


async def test_birthday_exceptions():
    # Clean up before test
    cleanup_test_files()

    birthdays = BirthdayJsonDB()

    try:
        # Test adding duplicate birthday raises exception
        await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-01"))

        with pytest.raises(BirthdayAlreadyExists):
            await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-02"))

        # Test removing non-existent birthday raises exception
        with pytest.raises(BirthdayDoesNotExist):
            await birthdays.remove_birthday(999, 1)
    finally:
        # Clean up after test
        cleanup_test_files()

