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
        return cls(role="user", content=content, name=name or "unknown")

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
        cls,
        message_history: MessageHistory,
        system_message: str,
        main_message: Optional[Message] = None,
    ) -> "GPTMessages":
        messages = cls.convert_to_gpt_messages(message_history)
        messages.insert(0, GPTMessage.system(system_message))
        if main_message:
            messages.append(
                GPTMessage.user(main_message.content, main_message.user.name)
            )
        return messages

    def to_gpt_list(self):
        return [message.to_openai_dict() for message in self]
