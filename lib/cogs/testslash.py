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
    Member, Embed, app_commands, Interaction, FFmpegPCMAudio, utils, app_commands, Object, HTTPException, Message
)

from discord import Object as DiscordObject
from discord import Message as DiscordMessage

from discord.ext.commands import (
    GroupCog, Cog, command, hybrid_command, cooldown, BucketType, BadArgument, guild_only, group, hybrid_group, is_owner, guild_only, Context, Greedy
)

from discord.ext import commands

from discord.ext import tasks

from discord.errors import HTTPException, ClientException

from datetime import date, datetime
import time

import re

from ..db import db
from ..dizzidb import Dizzidb, dbprefix

class Testslash(Cog):
            
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        #hacky solution to add context menus through cogs
        self.ctx_menu = app_commands.ContextMenu(name="React", callback=self.reactioncmnu, guild_ids=[762125363937411132],)
        self.bot.tree.add_command(self.ctx_menu)

    #hybrid command functions

    @commands.hybrid_group(fallback='get', description="Test2", usage="Testing Usage", brief="ccccccccccccccccccccccccccccccccccccccc")
    @app_commands.guilds(DiscordObject(762125363937411132))
    async def alpha(self, ctx: commands.Context) -> None:
        """test docstring for alphaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
        """
        await ctx.send("Alpha")

    @alpha.command()
    async def beta(self, ctx: commands.Context) -> None:
        await ctx.send("Beta")

    #context menu commands
    async def reactioncmnu(self, interaction:Interaction, message: DiscordMessage):
        await interaction.response.send_message('Very cool message!')

    #cleanup on cog unload  
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    #ready
    @Cog.listener()
    async def on_ready(self) -> None:
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("testslash")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Testslash(bot))