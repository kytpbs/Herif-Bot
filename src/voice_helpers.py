from queue import Queue
from typing import Any


class play_path_queue_guild:
    def __init__(self) -> None:
        self.queue_dict: dict[int, Queue[tuple[dict[str, Any], str]]] = {}

    def __hash__(self) -> int:
        return hash(self.queue_dict)

    def get_queue(self, guild_id: int) -> Queue[tuple[dict[str, Any], str]]:
        """returns the queue for the guild_id, if it doesn't exist, it creates an empty one

        Args:
            guild_id (int): the guild_id to get the queue for

        Returns:
            Queue[tuple[dict[str, Any], str]]: returns the queue that has the youtube_dl output and the path to the file
        """
        return self.queue_dict.setdefault(guild_id, Queue(8))

    def get(self, guild_id: int):
        return self.get_queue(guild_id).get()

    def set_queue(self, guild_id: int, queue: Queue[tuple[dict[str, Any], str]]):
        self.queue_dict[guild_id] = queue

    def append_to_queue(self, guild_id: int, item: tuple[dict[str, Any], str]):
        if self.get_queue(guild_id).full():
            raise ValueError("Queue is full")
        self.get_queue(guild_id).put(item)

    def task_done(self, guild_id: int):
        self.get_queue(guild_id).task_done()

    def empty(self, guild_id: int):
        return self.get_queue(guild_id).empty()

    def full(self, guild_id: int):
        return self.get_queue(guild_id).full()

    def clear_queue(self, guild_id: int):
        queue = self.get_queue(guild_id)
        with queue.mutex:
            queue.queue.clear()
            queue.all_tasks_done.notify_all()
            queue.unfinished_tasks = 0
