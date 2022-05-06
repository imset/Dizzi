from aiohttp import request
from typing import Optional, Literal
import asyncio
from random import (
    choice, randint
)
from mediawiki import (
    MediaWiki, exceptions
)

from discord import (
    Member, Embed, app_commands, Interaction, FFmpegPCMAudio, utils, app_commands, Object, HTTPException
)
from discord.ext.commands import (
    Cog, command, cooldown, BucketType, BadArgument, guild_only, group, is_owner, guild_only, Context, Greedy
)

from discord.ext import tasks

from discord.errors import HTTPException, ClientException

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

    @command(name="musicplay",
        aliases=["muplay","mp"],
        brief="Play some tunes",
        usage="`*PREF*mustop` - Please Stop The Music!\nExample: `*PREF*mustop`")
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
            #print(vc.is_playing())
            # while vc.is_playing():
            #     print(vc.is_playing())
            # print(vc.is_playing())
            # if not vc.is_playing():
            #     print (vc.is_playing())
            #     await voice_channel.disconnect()
        else:
            await ctx.send("Join a voice channel to use this command!")
        # Delete command after the audio is done playing.
        # await ctx.message.delete()

    @command(name="musicstop",
        aliases=["mustop","ms"],
        brief="Stops any playing music",
        usage="`*PREF*mustop` - Please Stop The Music!\nExample: `*PREF*mustop`")
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

    # @command(name="testsync",
    #     hidden=True)
    # @is_owner()
    # async def testsync(self, ctx):
    #     try:
    #         await ctx.bot.tree.sync(guild=Object(id=ctx.guild.id))
    #     except HTTPException as e:
    #         print(e)
    #         pass

    #     await ctx.send("Done")

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("music")
            
async def setup(bot):
    await bot.add_cog(Music(bot))
    #bot.tree.add_command(MusicSlash())