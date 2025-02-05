import discord
from src.voice.music_base import Music
from src.voice import download_manager


class AutoDownloadingMusic(Music):
    def __init__(self, music_id: str, title: str, thumbnail_url: str):
        super().__init__(music_id, title, thumbnail_url)

        download_manager.start_downloading(self)

    def is_downloaded(self):
        return download_manager.is_downloaded(self)

    def is_errored_out(self):
        return download_manager.is_errored_out(self)


class NoMoreMusic(Exception): ...


class MusicQueue:
    def __init__(self) -> None:
        self.queue: list[Music] = []
        self.currently_at = -1
        self.is_looped = False

    async def add_music(self, music: Music):
        """
        Adds a music to the end of the list
        """
        self.queue.append(music)

    async def play_next(self, music: Music):
        """
        Plays the music right after the current one, adding it into the loop if looped
        """
        self.queue.insert(self.currently_at + 1, music)

    def get_current_music(self) -> Music:
        if len(self.queue) == 0:
            raise ValueError("You called get_current_music before adding any music")
        return self.queue[max(0, self.currently_at)]

    def back_to_previous_music(self) -> Music:
        """
        Moves back to the previous music
        Will silently ignore if it can't go back

        Returns:
            Current_Music: returns the previous music for convenience,
            which now is `get_current_music`
        """
        # -1 is still 0, but we have to hold it at -1, if we are at the start, before the first music
        if (self.currently_at - 1) >= -1:
            self.currently_at -= 1
            return self.get_current_music()

        if self.is_looped or self.currently_at < 0:
            self.currently_at = len(self.queue) - 1
            return self.get_current_music()

        # At the start of list, and we are not looping
        # So we return the first music
        return self.get_current_music()

    def switch_to_next_music(self) -> Music:
        """
        Moves onto the next music
        Will raise an error if no more can be found

        Raises:
            NoMoreMusic: Raised if there is no music left in queue

        Returns:
            Current_Music: returns the next music for convenience,
            which now is `get_current_music`
        """
        if (self.currently_at + 1) < len(self.queue):
            self.currently_at += 1
            return self.get_current_music()

        if self.is_looped or self.currently_at < 0:
            self.currently_at = 0
            return self.get_current_music()

        # At the end of list, and we are not looping
        raise NoMoreMusic

    def clear(self):
        self.queue.clear()
        self.currently_at = -1

    def get_queue_str(self, highlighted_index = None) -> str:
        """
        returns the queue as a new line separated string
        give -1 to highlight nothing
        """
        queue_str = ""
        highlighted_index = highlighted_index or self.currently_at
        for index, music in enumerate(self.queue):
            if index == highlighted_index:
                queue_str += f"**-->  [{music.title}]({music.url})**\n"
            elif (music.is_downloaded()):
                queue_str += f"[{music.title}]({music.url})\n"
            else:
                queue_str += f"~~{music.title}({music.url})~~(indirilemedi, tekrar denenciek)\n"

        return queue_str

    def get_current_song_embed(self) -> discord.Embed:
        music = self.get_current_music()
        queue_str = self.get_queue_str()
        return (
            discord.Embed(
                title=f"Şu an Çalıyor: {music.title}",
                url=music.url,
                color=discord.Color.green(),
            )
            .set_thumbnail(url=music.thumbnail_url)
            .add_field(name="Liste", value=queue_str)
        )
