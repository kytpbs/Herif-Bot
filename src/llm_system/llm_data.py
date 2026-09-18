from dataclasses import dataclass


@dataclass
class User:
    name: str | None = None
    is_bot: bool = name is None


@dataclass
class Message:
    """
    A message object that contains the user, content, and server
    If the server_name is None, then the message is assumed to be a DM
    """

    user: User
    content: str
    server_name: str | None = None


class MessageHistory(list[Message]):
    pass
