import logging
import os
from sys import platform

import google.cloud.logging
from dotenv import load_dotenv

from Constants import BOT_NAME

load_dotenv()


def is_server(only_true_if_cloud: bool = True) -> bool:
    dev = os.getenv("DEV")
    cloud = os.getenv("CLOUD")
    is_cloud = cloud == "true"
    if cloud is not None:
        if not only_true_if_cloud or is_cloud:
            return is_cloud
    if dev is not None and dev == "true":
        return False
    return platform == "linux" or platform == "linux2"


if is_server(only_true_if_cloud=False):
    try:
        google_client = google.cloud.logging.Client()
        google_client.get_default_handler()
        google_client.setup_logging(log_level=logging.DEBUG)
    except Exception as e:
        logging.error("Failed to setup google cloud logging", exc_info=e)
else:
    format_string = '%(asctime)s: %(name)s - %(levelname)s - %(message)s in %(filename)s:%(lineno)d'
    logging.basicConfig(level=logging.DEBUG, filename=f'{BOT_NAME}.log', filemode='w', format=format_string)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.formatter = logging.Formatter(format_string)
    logging.getLogger().addHandler(console)
