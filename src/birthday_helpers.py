from datetime import datetime
import logging


def get_user_and_date_from_string(dictinary: dict[int, str]):
  new_dict = {}
  import src.client as client  # we import here to avoid circular imports
  client = client.get_client_instance()
  delete_non_users(dictinary)
  for user_id, date in dictinary.items():
    user = client.get_user(int(user_id))
    if user is None:
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
