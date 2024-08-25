import logging
import discord

from src.downloading_system import get_downloader

def _convert_paths_to_discord_files(paths: list[str]) -> list[discord.File]:
    return [discord.File(path) for path in paths]


def _get_shortest_punctuation_index(caption: str) -> int | None:
    # check if we have a punctuation mark in the caption
    dot = caption.find(".")
    comma = caption.find(",")
    question_mark = caption.find("?")
    exclamation_mark = caption.find("!")
    filtered_list = list(filter(lambda x: x != -1, [dot, comma, question_mark, exclamation_mark]))
    if len(filtered_list) == 0:
        return None
    return min(filtered_list)

def _get_shortened_caption(caption: str) -> str:
    # check if we have a punctuation mark in the caption
    caption = caption.split("\n")[0]

    punctuation_index = _get_shortest_punctuation_index(caption)
    if punctuation_index:
        return caption[:punctuation_index + 1]
    return caption[:100]


def _get_view(shortened_caption: str, caption: str):
    view = discord.ui.View()
    button = discord.ui.Button(label="🔽\nExpand", style=discord.ButtonStyle.secondary)
    async def callback(interaction: discord.Interaction):
        revert_view = discord.ui.View()
        button = discord.ui.Button(label="🔼\nShorten", style=discord.ButtonStyle.secondary)
        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(content=shortened_caption, view=view)
        button.callback = callback
        revert_view.add_item(button)
        await interaction.response.edit_message(content=caption, view=revert_view)
    button.callback = callback
    view.add_item(button)
    return view



async def download_video_command(interaction: discord.Interaction, url: str, is_ephemeral: bool = False, include_title: bool | None = None):
    downloader = get_downloader(url)
    if downloader is None:
        await interaction.response.send_message("Bu link desteklenmiyor", ephemeral=True)
        logging.info("Found an unsupported link: %s", url)
        return

    await interaction.response.defer(ephemeral=is_ephemeral)

    try:
        attachments = await downloader.download_video_from_link(url)
        file_paths = [attachment.path for attachment in attachments]
        discord_files = _convert_paths_to_discord_files(file_paths)
    except Exception as e:
        await interaction.followup.send("Bir şey ters gitti... lütfen tekrar deneyin", ephemeral=True)
        raise e # re-raise the exception so we can see what went wrong
    if len(attachments) == 0:
        await interaction.followup.send("Videoyu Bulamadım, lütfen daha sonra tekrar deneyin ya da hatayı bildirin", ephemeral=True)
        return
    returned_content = " + ".join(filter(None, [attachment.caption for attachment in attachments]))
    default_caption = f"Video{'s' if len(attachments) > 1 else ''} Downloaded"
    caption = ""
    view = discord.utils.MISSING
    shortened_content = _get_shortened_caption(returned_content) + " ***...***"

    if include_title is False or not returned_content:
        caption = default_caption

    elif include_title is True:
        caption = returned_content

    elif len(shortened_content) < len(returned_content):
        view = _get_view(shortened_content, returned_content)
        caption = shortened_content
    else:
        caption = returned_content

    await interaction.followup.send(caption, files=discord_files, ephemeral=is_ephemeral, view=view)
