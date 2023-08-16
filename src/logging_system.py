import logging
import os
from sys import platform

import google.cloud.logging
from dotenv import load_dotenv

from Constants import BOT_NAME

load_dotenv()


DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


def is_server(only_true_if_cloud: bool = True) -> bool:
    dev = os.getenv("DEV")
    cloud = os.getenv("CLOUD")
    is_cloud = cloud == "true" 
    if cloud is not None:
        if not only_true_if_cloud:
            return is_cloud
        elif is_cloud:
            return is_cloud
    if dev is not None and dev == "true":
        return False
    return platform == "linux" or platform == "linux2"


if is_server(only_true_if_cloud=False):
    google_client = google.cloud.logging.Client()
    google_client.setup_logging(log_level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG, filename=f'{BOT_NAME}.log')
logger = logging.getLogger(BOT_NAME)


def log(message: str, level: int = INFO):
    logger.log(level, message)
