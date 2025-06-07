import logging
import os
from sys import platform

import axiom_py
from axiom_py.logging import AxiomHandler

import google.cloud.logging
from dotenv import load_dotenv

from Constants import BOT_NAME

load_dotenv()
FORMAT_STRING = (
    "%(asctime)s %(levelname)s - %(name)s - %(message)s in %(filename)s:%(lineno)d"
)
_FORMATTER = logging.Formatter(FORMAT_STRING, datefmt="%Y-%m-%d %H:%M:%S")


def is_server(only_true_if_cloud: bool = True) -> bool:
    dev = os.getenv("DEV") or "false"

    is_cloud = any(
        (
            is_prod_str.lower() in ["true", "1", "yes"]
            for is_prod_str in map(os.getenv, ["CLOUD", "PROD", "IS_CLOUD", "IS_PROD"])
            if is_prod_str is not None
        )
    )

    if only_true_if_cloud:
        return is_cloud

    if dev == "true":
        return False

    return is_cloud or platform.startswith("linux")


def setup_file_logging():
    log_file = logging.FileHandler(
        filename=f"{BOT_NAME}.log",
        mode="w",
    )
    log_file.setLevel(logging.INFO)
    log_file.setFormatter(_FORMATTER)
    logging.getLogger().addHandler(log_file)


def setup_console_logging():
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(_FORMATTER)
    logging.getLogger().addHandler(console)


def setup_google_cloud_logging():
    try:
        google_client = google.cloud.logging.Client()
        google_client.get_default_handler()
        google_client.setup_logging(log_level=logging.DEBUG)
    except Exception as e:
        logging.error("Failed to setup google cloud logging", exc_info=e)


class ErrorHandlingAxiomHandler(AxiomHandler):
    """
    A custom AxiomHandler that handles errors during logging.
    This is useful to prevent the bot from crashing due to logging issues.
    """

    def __init__(self, client: axiom_py.Client, dataset: str):
        super().__init__(client, dataset)
        # Check if the dataset is valid before starting the handler, if not raise an error.
        # This should have been done by `AxiomHandler.__init__`, but it is not, so we do it here.
        # There is an issue for this here: https://github.com/axiomhq/axiom-py/issues/165
        try:
            client.datasets.get(
                self.dataset
            )  # This will raise an error if the dataset does not exist
        except axiom_py.client.AxiomError as e:
            raise axiom_py.client.AxiomError(
                e.status,
                axiom_py.client.AxiomError.Response(
                    f"{self.dataset}, does not exist", None
                ),
            )

    def emit(self, record):
        try:
            super().emit(record)
            # For some reason Axiom seems to throw a lot of errors, so to be safe, i will catch all exceptions
        except Exception as e:  # pylint: disable=broad-except
            logging.getLogger().removeHandler(self)
            logging.warning(
                "Failed to log to Axiom, most probably because DB name is wrong",
                exc_info=e,
            )
            logging.getLogger().addHandler(self)


def setup_axiom_logging():
    try:
        client = axiom_py.Client()
        handler = ErrorHandlingAxiomHandler(client, "herifbot")
    except axiom_py.client.AxiomError as e:
        logging.error("Failed to setup Axiom logging", exc_info=e)
        return
    logging.getLogger().addHandler(handler)
    try:
        logging.debug("Axiom logging setup successfully")
        handler.flush()  # force flush to test if the connection is actually working
    except axiom_py.client.AxiomError as e:
        logging.getLogger().removeHandler(handler)
        logging.error(
            "Failed to initialize axiom logging handler, removing it", exc_info=e
        )
        return


def setup_logging():
    setup_console_logging()

    if is_server(only_true_if_cloud=False):
        setup_google_cloud_logging()
    else:
        setup_file_logging()

    # Both google cloud and axiom logging can throw exceptions, so we should
    # be able to see if any one of them fails while one worked,

    setup_axiom_logging()
