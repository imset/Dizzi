import asyncio
import yt_dlp as youtube_dl
from discord import (
    Member, Embed, Interaction, FFmpegPCMAudio, utils
)
import discord
from discord.ext.commands import (
    Cog, command, cooldown, guild_only
)
from discord.errors import ClientException

#thanks to https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

queueset = []

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

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
        if not isinstance(ctx.author.voice, type(None)):
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


    @command(name="join",
        hidden=True)
    @guild_only()
    async def join(self, ctx):
        """Joins a voice channel"""
        # if ctx.voice_client is not None:
        #     return await ctx.voice_client.move_to(channel)

        # await channel.connect()
        if not isinstance(ctx.author.voice, type(None)):
            voice_channel = ctx.author.voice.channel
            channel = voice_channel.name
            try:
                vc = await voice_channel.connect()
            except ClientException:
                await ctx.send(f"Sorry, I'm currently busy playing music in the channel \"{ctx.guild.voice_client.channel.name}\"")
                return
            #vc.play(FFmpegPCMAudio(executable="C:/Users/HWool/Documents/My Programs/DiscordBot/Dizzi/ffmpeg/bin/ffmpeg.exe", source="C:/Users/HWool/Music/dearmaria/dearmaria.mp3"))
            # Sleep while audio is playing.
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
        else:
            await ctx.send("Join a voice channel to use this command!")
        # Delete command after the audio is done playing.
        # await ctx.message.delete()

    @command(name="queue",
        aliases=["q"],
        brief="Play some tunes from the tube",
        hidden=True)
    @guild_only()
    async def ytqueue(self, ctx, *, url):
        """Joins channel then plays from a url (almost anything youtube_dl supports)"""

        #old code: only plays one song at a time

        # async with ctx.typing():
        #     player = await YTDLSource.from_url(url, loop=self.bot.loop)

        # if not isinstance(ctx.author.voice, type(None)):
        #     voice_channel = ctx.author.voice.channel
        #     channel = voice_channel.name
        #     try:
        #         vc = await voice_channel.connect()
        #     except ClientException:
        #         await ctx.send(f"Sorry, I'm currently busy playing music in the channel \"{ctx.guild.voice_client.channel.name}\"")
        #         return
        #     vc.play(FFmpegPCMAudio(executable="C:/Users/HWool/Documents/My Programs/DiscordBot/Dizzi/ffmpeg/bin/ffmpeg.exe", source="C:/Users/HWool/Music/dearmaria/dearmaria.mp3"))
        #     ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        #     await ctx.send(f'Now playing: {player.title}')
        #     # Sleep while audio is playing.
        #     while vc.is_playing():
        #         await asyncio.sleep(1)
        #     await vc.disconnect()
        # else:
        #     await ctx.send("Join a voice channel to use this command!")

        # new code: queue system

        try:
            print(1)
            voice_channel = ctx.author.voice.channel
            vc = await voice_channel.connect()
            queueset.append(url)
            print(2)
        except AttributeError:
            print(3)
            await ctx.send("Join a voice channel to use this command!")
        except ClientException:
            print(4)
            if voice_channel.name != ctx.guild.voice_client.channel.name:
                await ctx.send(f"Sorry, I'm currently busy playing music in the channel \"{ctx.guild.voice_client.channel.name}\"")
            else:
                # author is in the same voice channel as bot, can continue
                vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
                queueset.append(url)
                pass

        print(queueset)
        await ctx.send(f'Queing Song')

        while len(queueset) != 0:
            if vc.is_playing():
                async with ctx.typing():
                    player = await YTDLSource.from_url(queueset[0], loop=self.bot.loop)
                    #await ctx.send("Song queued")
            else:
                async with ctx.typing():
                    player = await YTDLSource.from_url(queueset[0], loop=self.bot.loop)
                #vc.play(FFmpegPCMAudio(executable="C:/Users/HWool/Documents/My Programs/DiscordBot/Dizzi/ffmpeg/bin/ffmpeg.exe", source="C:/Users/HWool/Music/dearmaria/dearmaria.mp3"))
                try:
                    ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                    await ctx.send(f'Now playing: {player.title}')
                except ClientException:
                    pass
                # Sleep while audio is playing.
                while vc.is_playing() and queueset[0] != 'SKIP':
                    await asyncio.sleep(1)
                    print(queueset[0])
                if vc.is_playing():
                    vc.stop()
                    print("stophit")
                queueset.pop(0)


        print("while exited")
        await asynchio.sleep(3)
        if len(queueset == 0):
            await vc.disconnect()


        # if not isinstance(ctx.author.voice, type(None)):
        #     voice_channel = ctx.author.voice.channel
        #     channel = voice_channel.name
        #     try:
        #         vc = await voice_channel.connect()
        #     except ClientException:
        #         await ctx.send(f"Sorry, I'm currently busy playing music in the channel \"{ctx.guild.voice_client.channel.name}\"")
        #         return



    @command(name="stop",
        aliases=["ytstop", "ytst"],
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
                #await vc.disconnect()
            else:
                await ctx.send("Error: Must be in the same voice channel.")

    @command(name="skip",
        aliases=["ytskip", "ytsk"],
        brief="Stops any playing music",
        usage="`*PREF*mustop` - Please Stop The Music!\nExample: `*PREF*mustop`",
        hidden=True)
    @guild_only()
    async def muskip(self, ctx):
        """Stops whatever music Dizzi is playing. You must be in the same channel as Dizzi to do this."""
        vc = utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc == None or vc.is_playing() != True:
            await ctx.send("I'm not currently playing any music in this server!")
        else:
            if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                queueset[0] = "SKIP"
                print(queueset)
                #vc.stop()
                #await vc.disconnect()
            else:
                await ctx.send("Error: Must be in the same voice channel.")

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("music")
            
async def setup(bot):
    await bot.add_cog(Music(bot))