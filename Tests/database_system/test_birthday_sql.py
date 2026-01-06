import asyncio
from datetime import UTC, date, datetime
from sys import platform

import pytest

from src.sql.postgres import PostgresDBClient
from src.data.birthdays import BirthdayAlreadyExists
from src.data.providers.birthday_sql import BirthdaySQL


@pytest.fixture(scope="module")
def event_loop_policy(request: pytest.FixtureRequest):
    del request  # Unused parameter, but required by pytest fixture signature
    if platform == "win32":
        # psycopg3 does not support the default event loop policy on Windows
        # So when using windows we have to use the WindowsSelectorEventLoopPolicy
        return asyncio.WindowsSelectorEventLoopPolicy()
    return asyncio.DefaultEventLoopPolicy()


async def test_get_birthdays():
    client = PostgresDBClient()

    birthdays = await BirthdaySQL.create(client)

    await birthdays.add_birthday(1, 1, date.fromisoformat("2023-01-01"))
    await birthdays.add_birthday(2, 1, date.fromisoformat("2023-01-02"))

    # Make sure today is at UTC since its also checked for UTC in DB
    today = datetime.now(UTC).date()
    birthday = date(2000, today.month, today.day)

    await birthdays.add_birthday(3, 1, birthday)

    assert len(await birthdays.get_birthdays_in_guild(1)) == 3
    assert len(await birthdays.get_birthdays_today(1)) == 1

    assert await birthdays.get_birthday(1, 1) == date.fromisoformat("2023-01-01")

    await birthdays.remove_birthday(3, 1)

    await asyncio.sleep(0.5)  # Ensure cache is not used

    assert await birthdays.get_birthday(3, 1) is None
    assert len(await birthdays.get_birthdays_today(1)) == 0

    # Clean up
    await birthdays.remove_birthday(1, 1)
    await birthdays.remove_birthday(2, 1)

    await client.close()


async def test_duplicate_birthday_addition():
    client = PostgresDBClient()

    birthdays = await BirthdaySQL.create(client)

    await birthdays.add_birthday(4, 1, date.fromisoformat("2023-01-01"))

    with pytest.raises(BirthdayAlreadyExists):
        # Adding the same birthday again should raise an exception
        await birthdays.add_birthday(4, 1, date.fromisoformat("2023-01-01"))

    with pytest.raises(BirthdayAlreadyExists):
        # Adding the same birthday again with different date should also raise an exception
        await birthdays.add_birthday(4, 1, date.fromisoformat("2024-02-02"))

    assert await birthdays.get_birthdays_for_user(4) == [date(2023, 1, 1)]

    await birthdays.remove_birthday(4, 1)

    await client.close()
