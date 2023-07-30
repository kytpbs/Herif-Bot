from datetime import datetime


def get_user_and_date_from_string(dictinary: dict):
  new_dict = {}
  import client
  client = client.get_client_instance()
  for user_id, date in dictinary.items():
    user = client.get_user(int(user_id))
    if user is None:
      continue
    dates = date.split("-")
    if len(dates) != 3:
      e = ValueError("Unknown date format, Please fix!")
      print(e)
      continue
    date_obj = datetime(int(dates[0]), int(dates[1]), int(dates[2]))
    print(f"{user} : {date_obj}")
    if date_obj is None:
      continue
    new_dict[user] = date_obj

  return new_dict
