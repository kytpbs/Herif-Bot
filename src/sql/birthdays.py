from datetime import date
from src.sql.sql_errors import NotConnectedError, AlreadyExistsError
from src.sql.sql_wrapper import LOGGER, get, post


def get_all_birthdays(guild_id: str | None = None) -> list[tuple[int, date]]:
    sql_query = "SELECT user_id, birthday FROM birthdays"
    values = None
    if guild_id:
        sql_query += " WHERE guild_id = %s"
        values = (guild_id,)
    result = get(sql_query, values)
    if not result:
        return []
    return result

def get_birthday(user_id: str, guild_id: str | None = None) -> date | None:
    values = [user_id]
    sql_query = "SELECT birthday FROM birthdays WHERE user_id = %s"
    if guild_id:
        sql_query += " AND guild_id = %s"
        values.append(guild_id)
    result = get(sql_query, values)
    if not result or not result[0]:
        return None
    return result[0][0]

def get_users_birthday(birthday: date, guild_id: str | None = None) -> list[int]:
    values: list[str | date] = [birthday]
    sql_query = "SELECT user_id FROM birthdays WHERE birthday = %s"
    if guild_id:
        sql_query += " AND guild_id = %s"
        values.append(guild_id)
    result = get(sql_query, values)
    if not result:
        return []
    return [user_id for user_id, _ in result]

def add_birthday(user_id: str, birthday: date, guild_id: str) -> int:
    if get_birthday(user_id, guild_id):
        raise AlreadyExistsError(f"User {user_id} already has a birthday in the database")
    if guild_id:
        return post("INSERT INTO birthdays (user_id, birthday, guild_id) VALUES (%s, %s, %s);", (user_id, birthday, guild_id))
    return post("INSERT INTO birthdays (user_id, birthday) VALUES (%s, %s);", (user_id, birthday))


def create_table_if_not_exists():
    query = """
    CREATE TABLE IF NOT EXISTS birthdays (
        user_id BIGINT PRIMARY KEY,
        birthday DATE NOT NULL,
        guild_id BIGINT
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    post(query)

def sync_birthdays_dict_to_db(birthdays: dict[str, date], guild_id: str):
    rows = 0

    for user_id, birthday in birthdays.items():
        if get_birthday(user_id, guild_id):
            LOGGER.debug(f"User {user_id} already has a birthday in the database, skipping...")
            continue
        rows+= add_birthday(user_id, birthday, guild_id)

    return rows

try:
    create_table_if_not_exists()
except NotConnectedError:
    LOGGER.warning("NO CONNECTION TO DATABASE, CANNOT CREATE TABLE")
