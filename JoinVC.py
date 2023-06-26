import discord
import json

class join:
    def __init__(self, client: discord.Client):
        self.client = client
    
    async def join_voice_channel(self, interaction: discord.Interaction = None, channel: discord.VoiceChannel = None, member: discord.Member = None, force: bool = False):
        
        if interaction is not None:
            if isinstance(interaction.user) is not discord.Member:
                data = RuntimeError("Kullanıcı bir üye değil")
            if interaction.user.voice is None:
                data = RuntimeError("Kullanıcı bir ses kanalında değil")
            
            channel = interaction.user.voice.channel
            data = await self.join_voice_channel_from_channel(channel)
        
       
       
        elif channel is not None:
            data = await self.join_voice_channel_from_channel(channel)
            
        
        elif member is not None:
            if member.voice is None:
                status = "failed"
                details = "member is not in a voice channel"
                data = {"status": status, "details": details}
            channel = member.voice.channel
            data = await self.join_voice_channel_from_channel(channel)
        return json.dumps(data)
    
    async def join_voice_channel_from_channel(channel: discord.VoiceChannel, force: bool = False):
        if channel is None:
            status = "failed"
            details = "channel not found"
        
        if channel.guild.voice_client is not None:
            if channel.guild.voice_client.channel.id == channel.id:
                status = "connected"
                vc_client = channel.guild.voice_client
            
            else:
                if force:
                    await channel.guild.voice_client.disconnect()
                    vc_client = await channel.connect()
                    status = "connected"
                else:
                    status = "failed"
                    details = "already connected to another channel in the same server"

        
        data = {
                    "status": status,
                    "channel_mention": channel.mention,
                    "voice_client": vc_client
                }
        if details is not None:
            data["details"] = details
        return data


if __name__ == "__main__":
    print("This file is not meant to be run directly!")
    print("Please run main.py instead")
    exit()