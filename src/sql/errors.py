class SQLError(Exception):
    pass


class NotConnectedError(SQLError):
    pass


class SQLFailedMiserably(SQLError):
    pass


class AlreadyExists(SQLError):
    pass
