from typing import Final, Self
import discord


class CaptionView(discord.ui.View):
    def __init__(self, caption: str, short_caption: str):
        super().__init__(timeout=None)
        self.full_caption: Final = caption
        self.short_caption: Final = short_caption
        # This view doesn't exist if the caption was short enough
        # So expanded is False initially if the view was created
        self.expanded: bool = False

    @property
    def caption(self) -> str:
        return self.full_caption if self.expanded else self.short_caption

    @discord.ui.button(
        label="Expand", emoji="🔽", style=discord.ButtonStyle.secondary
    )
    async def toggle_button(
        self, interaction: discord.Interaction, button: discord.ui.Button[Self]
    ):
        self.expanded = not self.expanded
        button.label = "Shorten" if self.expanded else "Expand"
        button.emoji = "🔼" if self.expanded else "🔽"
        _ = await interaction.response.edit_message(content=self.caption, view=self)
        return self
