
class SQLError(Exception):
    pass

class NotConnectedError(SQLError):
    pass

class SQLFailedMiserably(SQLError):
    pass


# Implementation specific errors
class AlreadyExistsError(Exception):
    pass

class TooManyAnswersError(Exception):
    def __init__(self, message, current_answer: list[str]) -> None:
        super().__init__(message)
        self.current_answers = current_answer
