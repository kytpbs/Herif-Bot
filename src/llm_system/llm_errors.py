from typing import Optional


class LLMError(Exception):
    """Base exception for any errors created in downloading."""

    msg = None

    def __init__(self, msg=None):
        if msg is not None:
            self.msg = msg
        elif self.msg is None:
            self.msg = type(self).__name__
        super().__init__(self.msg)


class NoTokenError(LLMError):
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "No API Key Found")


class APICallFailedError(LLMError):
    pass


class RanOutOfMoneyError(APICallFailedError):
    pass
