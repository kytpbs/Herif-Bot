from dataclasses import dataclass
import json
from typing import Literal, NamedTuple, Optional, Self, TypedDict, Union


@dataclass
class User:
    name: Optional[str] = None
    is_bot: bool = name is None


@dataclass
class Message:
    """
    A message object that contains the user, content, and server
    If the server_name is None, then the message is assumed to be a DM
    """

    user: User
    content: str
    server_name: Optional[str] = None


class MessageHistory(list[Message]):
    pass

class _GPTUserMessageDict(TypedDict):
    role: Literal["system", "assistant", "user"]
    content: str
    name: Optional[str]

class _GPTSystemMessageDict(TypedDict):
    role: Literal["system", "assistant", "user"]
    content: str

_GPTMessageDict = Union[_GPTUserMessageDict, _GPTSystemMessageDict]

class GPTMessage(NamedTuple):
    role: Literal["system", "assistant", "user"]
    content: str
    name: Optional[str] = None

    @classmethod
    def system(cls, content: str) -> "GPTMessage":
        return cls(role="system", content=content)

    @classmethod
    def assistant(cls, content: str) -> "GPTMessage":
        return cls(role="assistant", content=content)

    @classmethod
    def user(cls, content: str, name: str | None) -> "GPTMessage":
        return cls(role="user", content=content, name=name or "unknown")

    def to_dict(self) -> _GPTMessageDict:
        if self.name:
            return {
                "role": self.role,
                "content": self.content,
                "name": self.name,
            }
        return {
            "role": self.role,
            "content": self.content,
        }

class MainMessage(Message):
    pass

class GPTMessages(list[GPTMessage]):
    @classmethod
    def convert_to_gpt_messages(cls, message_history: MessageHistory) -> "GPTMessages":
        messages = GPTMessages()
        for message in message_history:
            if message.user.is_bot or message.user.name is None:
                messages.append(GPTMessage.assistant(message.content))
            else:
                messages.append(GPTMessage.user(message.content, message.user.name))
        return messages

    @classmethod
    def convert_and_merge(
        cls, message_history: MessageHistory, system_message: str, main_message: Optional[Message] = None
    ) -> "GPTMessages":
        messages = cls.convert_to_gpt_messages(message_history)
        messages.insert(0, GPTMessage.system(system_message))
        if main_message:
            messages.append(GPTMessage.user(main_message.content, main_message.user.name))
        return messages

    def to_gpt_list(self):
        return [message.to_dict() for message in self]
