import logging

import discord


# noinspection PyMethodMayBeStatic
class MyClient(discord.Client):

    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.deleted = False
        self.synced = False
        self.old_channel = None

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            import src.commands as commands  # pylint: disable=import-outside-toplevel # to avoid circular imports
            tree = commands.get_tree_instance()
            await tree.sync()
            self.synced = True
        logging.info("Logged on as %s", self.user)

client = MyClient()


def get_client_instance():
    return client
