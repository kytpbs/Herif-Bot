class SQLError(Exception):
    pass

class MalformedSQLDataReceived(SQLError):
    pass

class NotConnectedError(SQLError):
    pass


class SQLFailedMiserably(SQLError):
    pass


class AlreadyExists(SQLError):
    pass
