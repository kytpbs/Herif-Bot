class NoGuildContextInGuildCommandError(Exception):
    """Raised when a command that requires a guild is invoked outside of a guild context."""
    def __init__(self, message: str = "This command can only be used in a guild context"):
        super().__init__(message)
