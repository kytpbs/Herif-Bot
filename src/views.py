import discord

from src import voice_commands


class voice_play_view(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_buttons()
        
    def add_buttons(self):
        pause_button = discord.ui.Button(label="⏸️", style=discord.ButtonStyle.gray, custom_id="pause", row=0)
        skip_button = discord.ui.Button(label="⏭️", style=discord.ButtonStyle.secondary, custom_id="skip", row=1)
        leave_button = discord.ui.Button(label="Çık", style=discord.ButtonStyle.danger, custom_id="exit", row=2)
        
        async def pause_callback(interaction: discord.Interaction):
            await voice_commands.pause(interaction, edit=True)
        
        async def skip_callback(interaction: discord.Interaction):
            await voice_commands.next_song(interaction, edit=True)
        
        pause_button.callback = pause_callback
        skip_button.callback = skip_callback
        leave_button.callback = voice_commands.leave
        
        self.add_item(pause_button)
        self.add_item(skip_button)
        self.add_item(leave_button)

class voice_pause_view(discord.ui.View):
  def __init__(self, *, timeout = 180):
    super().__init__(timeout=timeout)
    self.add_buttons()
  
  def add_buttons(self):
    resume_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="resume")
    
    async def resume_callback(interaction: discord.Interaction):
      await voice_commands.resume(interaction, edit=True)
    
    resume_button.callback = resume_callback
    
    self.add_item(resume_button)

class voice_over_view(discord.ui.View):
  def __init__(self, *, timeout = 180):
      super().__init__(timeout=timeout)
      self.add_buttons()
  
  def add_buttons(self):
    leave_button = discord.ui.Button(label="Çık", style=discord.ButtonStyle.danger, custom_id="exit")
    
    leave_button.callback = voice_commands.leave
    self.add_item(leave_button)
