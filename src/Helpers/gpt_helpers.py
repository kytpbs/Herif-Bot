class GPTError:
    def __init__(self, error_message) -> None:
        self.error_message = error_message

    def __str__(self) -> str:
        return self.error_message
