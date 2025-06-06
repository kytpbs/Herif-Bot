import logging
import os
from sys import platform

import google.cloud.logging
from dotenv import load_dotenv

from Constants import BOT_NAME

load_dotenv()


def is_server(only_true_if_cloud: bool = True) -> bool:
    dev = os.getenv("DEV")
    is_cloud = any(
        (
            is_prod_str.lower() in ["true", "1", "yes"]
            for is_prod_str in map(os.getenv, ["CLOUD", "PROD", "IS_CLOUD", "IS_PROD"])
            if is_prod_str is not None
        )
    )
    if is_cloud:
        if not only_true_if_cloud or is_cloud:
            return is_cloud
    if dev is not None and dev == "true":
        return False
    return platform == "linux" or platform == "linux2"


def setup_logging():
    format_string = (
        "%(asctime)s: %(name)s - %(levelname)s - %(message)s in %(filename)s:%(lineno)d"
    )
    formatter = logging.Formatter(format_string)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.formatter = formatter

    logging.getLogger().addHandler(console)

    log_file = logging.FileHandler(
        filename=f"{BOT_NAME}.log",
        mode="w",
    )
    log_file.setLevel(logging.INFO)
    log_file.formatter = formatter
    logging.getLogger().addHandler(log_file)

    if is_server(only_true_if_cloud=False):
        try:
            google_client = google.cloud.logging.Client()
            google_client.get_default_handler()
            google_client.setup_logging(log_level=logging.DEBUG)
        except Exception as e:
            logging.error("Failed to setup google cloud logging", exc_info=e)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            filename=f"{BOT_NAME}.log",
            filemode="w",
            format=format_string,
        )
