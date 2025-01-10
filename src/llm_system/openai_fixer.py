import string
from typing import Literal, NamedTuple, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from src.llm_system.llm_data import Message, MessageHistory


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
        return cls(role="user", content=content, name=_sanitize_name(name or ""))

    def to_openai_dict(self) -> ChatCompletionMessageParam:
        """
        Convert the GPTMessage to a dictionary that can be used in the API call
        This is due to openai's typing system using TypedDicts, instead of NamedTuples which are more pythonic
        So this workaround is needed to convert the NamedTuple to a TypedDict

        Returns:
            GPTMessage: A dictionary that can be used in the API call
        """
        if self.role == "system":
            return {"content": self.content, "role": "system"}
        if self.role == "assistant":
            return {"content": self.content, "role": "assistant"}

        # user
        if self.name:
            return {"content": self.content, "role": "user", "name": self.name}
        return {"content": self.content, "role": "user"}


def _sanitize_name(name: str):
    # OpenAI Allowed String Regex: " ^[a-zA-Z0-9_-]+$'. "
    allowed_chars = list(string.ascii_letters + string.digits) + ["_", "-"]
    filtered = filter(lambda char: char in allowed_chars, name)
    return "".join(filtered)


class GPTMessages(list[GPTMessage]):
    @classmethod
    def _convert_to_gpt_messages(cls, message_history: MessageHistory) -> "GPTMessages":
        messages = GPTMessages()
        for message in message_history:
            if message.user.is_bot or message.user.name is None:
                messages.append(GPTMessage.assistant(message.content))
            else:
                messages.append(GPTMessage.user(message.content, message.user.name))
        return messages

    @classmethod
    def from_message_history(
        cls,
        message_history: MessageHistory,
        system_message: Optional[str] = None,
        main_message: Optional[Message] = None,
    ) -> "GPTMessages":
        messages = cls._convert_to_gpt_messages(message_history)
        if system_message:
            messages.insert(0, GPTMessage.system(system_message))
        if main_message:
            messages.append(
                GPTMessage.user(main_message.content, main_message.user.name)
            )
        return messages

    def to_gpt_list(self):
        """
        Convert the GPTMessages to a dictionary list that can be used in the API call
        This is due to openai's typing system using TypedDicts, instead of NamedTuples which are more pythonic
        So this workaround is needed to convert the NamedTuple to a TypedDict

        IF this object is used in the API call, it will work as expected just that typing will throw an error

        Returns:
            list[dict]: A list of dictionaries that openai library likes
        Warning:
            THIS FUNCTION WILL HAVE AN IMPACT ON PERFORMANCE, USE IT IF YOU DON'T CARE ABOUT PERFORMANCE,
            OR ELSE DIRECTLY PASS THIS OBJECT TO THE API CALL, AND IGNORE THE TYPING ERROR
        """
        return [message.to_openai_dict() for message in self]
