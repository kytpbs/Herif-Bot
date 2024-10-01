
from datetime import date

class SQLError(Exception):
    pass

class NotConnectedError(SQLError):
    pass

class SQLFailedMiserably(SQLError):
    pass


# Implementation specific errors
class AlreadyExistsError(Exception):
    def __init__(self, message: str, existent_data) -> None:
        super().__init__(message)
        self.existent_data = existent_data

    def get_existent_data(self):
        return self.existent_data

class BirthdayAlreadyExistsError(AlreadyExistsError):
    def __init__(self, message: str, existent_data: date) -> None:
        super().__init__(message, existent_data)

    @property
    def birthday(self) -> date:
        return self.get_existent_data()

class AlreadyRespondsTheSameError(AlreadyExistsError):
    def __init__(self, message: str, current_answer: str) -> None:
        super().__init__(message, current_answer)

    @property
    def current_answer(self) -> str:
        return self.get_existent_data()

class TooManyAnswersError(AlreadyExistsError):
    def __init__(self, message, current_answer: list[str]) -> None:
        super().__init__(message, current_answer)

    @property
    def current_answers(self) -> list[str]:
        return self.get_existent_data()
