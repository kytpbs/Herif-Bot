from datetime import datetime
import logging

import discord


def get_user_and_date_from_string(
    dictinary: dict[int, str], guild_to_check: discord.Guild | None = None
) -> dict[discord.User | discord.Member, datetime]:
    new_dict = {}
    member = None
    import src.client as client  # we import here to avoid circular imports

    client = client.get_client_instance()

    for user_id, date in dictinary.items():
        user = client.get_user(int(user_id))
        if guild_to_check is not None:
            member = guild_to_check.get_member(int(user_id))
        if user is None and member is None:
            continue
        dates = date.split("-")
        if len(dates) != 3:
            e = ValueError("Unknown date format, Please fix!")
            logging.error(e, date, dates, stack_info=True)
            continue
        date_obj = datetime(int(dates[0]), int(dates[1]), int(dates[2]))
        print(f"{user} : {date_obj}")
        if date_obj is None:
            continue
        if member is not None:
            new_dict[member] = date_obj
        else:
            new_dict[user] = date_obj

    return new_dict


def delete_non_users(dictinary: dict[int, str]) -> None:
    """Clears non-users from the dictinary

    Args:
        dictinary (dict[int, str]): the dictinary to clean
    """
    import src.client as client  # we import here to avoid circular imports

    client = client.get_client_instance()
    for user_id in dictinary.keys():
        user = client.get_user(int(user_id))
        if user is None:
            del dictinary[user_id]
            logging.debug(f"Deleted {user_id} from dictinary")
