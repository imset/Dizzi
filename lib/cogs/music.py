import asyncio
from discord import (
    Member, Embed, Interaction, FFmpegPCMAudio, utils
)
from discord.ext.commands import (
    Cog, command, cooldown, guild_only
)
from discord.errors import ClientException

class Music(Cog):
    """Test description for music cog"""
    def __init__(self, bot):
        self.bot = bot

    @command(name="musicplay",
        aliases=["muplay","mp"],
        brief="Play some tunes",
        usage="`*PREF*mustop` - Please Stop The Music!\nExample: `*PREF*mustop`",
        hidden=True)
    @guild_only()
    async def mustest(self, ctx):
        # Gets voice channel of message author
        if ctx.author.voice.channel != None:
            voice_channel = ctx.author.voice.channel
            channel = voice_channel.name
            try:
                vc = await voice_channel.connect()
            except ClientException:
                await ctx.send(f"Sorry, I'm currently busy playing music in the channel \"{ctx.guild.voice_client.channel.name}\"")
                return
            vc.play(FFmpegPCMAudio(executable="C:/Users/HWool/Documents/My Programs/DiscordBot/Dizzi/ffmpeg/bin/ffmpeg.exe", source="C:/Users/HWool/Music/dearmaria/dearmaria.mp3"))
            # Sleep while audio is playing.
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
        else:
            await ctx.send("Join a voice channel to use this command!")
        # Delete command after the audio is done playing.
        # await ctx.message.delete()

    @command(name="musicstop",
        aliases=["mustop","ms"],
        brief="Stops any playing music",
        usage="`*PREF*mustop` - Please Stop The Music!\nExample: `*PREF*mustop`",
        hidden=True)
    @guild_only()
    async def mustop(self, ctx):
        """Stops whatever music Dizzi is playing. You must be in the same channel as Dizzi to do this."""
        vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc == None or vc.is_playing() != True:
            await ctx.send("I'm not currently playing any music in this server!")
        else:
            if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                vc.stop()
                await vc.disconnect()
            else:
                await ctx.send("Error: Must be in the same voice channel.")

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("music")
            
async def setup(bot):
    await bot.add_cog(Music(bot))