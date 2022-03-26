from aiohttp import request
import asyncio
from random import (
    choice, randint
)
from mediawiki import (
    MediaWiki, exceptions
)

from discord import (
    Member, Embed, app_commands, Interaction, FFmpegPCMAudio
)
from discord.ext.commands import (
    Cog, command, cooldown, BucketType, BadArgument
)

from discord.ext import tasks

from discord.errors import HTTPException

from datetime import date, datetime
import time

import re

from ..db import db
from ..dizzidb import Dizzidb, dbprefix

class Music(Cog):
    """Test description for music cog"""
    def __init__(self, bot):
        self.bot = bot
        # tree = bot.tree

    @command(name="mustest")
    async def mustest(self, ctx):
        # Gets voice channel of message author
        voice_channel = ctx.author.voice.channel
        channel = None
        if voice_channel != None:
            channel = voice_channel.name
            vc = await voice_channel.connect()
            vc.play(FFmpegPCMAudio(executable="C:/Users/HWool/Documents/My Programs/DiscordBot/Dizzi/ffmpeg/bin/ffmpeg.exe", source="C:/Users/HWool/Music/dearmaria/dearmaria.mp3"))
            # Sleep while audio is playing.
            while vc.is_playing():
                await asyncio.sleep(1)
            await vc.disconnect()
            #print(vc.is_playing())
            # while vc.is_playing():
            #     print(vc.is_playing())
            # print(vc.is_playing())
            # if not vc.is_playing():
            #     print (vc.is_playing())
            #     await voice_channel.disconnect()
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")
        # Delete command after the audio is done playing.
        await ctx.message.delete()

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("music")
            
def setup(bot):
    bot.add_cog(Music(bot))