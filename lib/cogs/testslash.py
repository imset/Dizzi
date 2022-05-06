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
    GroupCog, Cog, command, hybrid_command, cooldown, BucketType, BadArgument, guild_only, group, hybrid_group, is_owner, guild_only, Context, Greedy
)

from discord.ext import tasks

from discord.errors import HTTPException, ClientException

from datetime import date, datetime
import time

import re

from ..db import db
from ..dizzidb import Dizzidb, dbprefix

class Testslash(GroupCog):
    """Test description for testslash cog"""
    def __init__(self, bot):
        self.bot = bot


    @hybrid_group(fallback='get')
    @app_commands.guild_only()
    async def testslash(self, ctx):
        await ctx.send("Hello!")

    @testslash.command()
    async def two(self, ctx):
        await ctx.send("Hello Again!")


    @GroupCog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("testslash")

    @command(name="testsync",
            aliases=["ts"],
            hidden=True)
    @is_owner()
    @guild_only()
    async def testsync(self, ctx):
        try:
            await self.bot.tree.sync(guild=ctx.guild)
        except HTTPException as e:
            print(e)
            pass

        await ctx.send("Done")
            
async def setup(bot):
    await bot.add_cog(Testslash(bot))