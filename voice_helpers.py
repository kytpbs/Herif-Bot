from queue import Queue
from typing import Any


class play_path_queue_guild:
    def __init__(self) -> None:
        self.queue_dict: dict[int, Queue[tuple[dict[str, Any], str]]] = {}

    def get_queue(self, guild_id: int):
        return self.queue_dict.get(guild_id, Queue(8))

    def get(self, guild_id: int):
        return self.get_queue(guild_id).get()

    def set_queue(self, guild_id: int, queue: Queue[tuple[dict[str, Any], str]]):
        self.queue_dict[guild_id] = queue

    def append_to_queue(self, guild_id: int, item: tuple[dict[str, Any], str]):
        self.get_queue(guild_id).put(item)

    def task_done(self, guild_id: int):
        self.get_queue(guild_id).task_done()

    def empty(self, guild_id: int):
        return self.get_queue(guild_id).empty()

    def full(self, guild_id: int):
        return self.get_queue(guild_id).full()
