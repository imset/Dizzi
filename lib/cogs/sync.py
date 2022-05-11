import discord
from discord import (
    Intents, Guild, channel, Embed, File
)
from discord.ext import commands
from discord.ext.commands import (
    Cog, command, Context, is_owner, guild_only,
    CommandNotFound, BadArgument, MissingRequiredArgument, 
    CommandOnCooldown, DisabledCommand, CheckFailure
)
from discord.errors import (
    HTTPException, Forbidden
)
from ..db import db
from ..dizzidb import Dizzidb

class Sync(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="testsync",
            aliases=["ts"],
            hidden=True)
    @is_owner()
    @guild_only()
    async def testsync(self, ctx):
        """syncs guild commands to test guild."""
        try:
            await self.bot.tree.sync(guild=discord.Object(762125363937411132))
            await ctx.send("Sync to Test Server finished")
        except HTTPException as e:
            print(e)
            pass

    @command(name="globalsync",
            aliases=["gs"],
            hidden=True)
    @is_owner()
    @guild_only()
    async def globalsync(self, ctx):
        """syncs global commands to all guilds"""
        try:
            await self.bot.tree.sync()
            await ctx.send("Global sync finished")
        except HTTPException as e:
            print(e)
            pass

    @command(name="nuclearoption",
            aliases=["nono"],
            hidden=True)
    @is_owner()
    @guild_only()
    async def nukecommands(self, ctx):
        """wipes bot's commands"""
        await self.bot.http.bulk_upsert_global_commands(588587478970269717, [])
        await self.bot.http.bulk_upsert_guild_commands(588587478970269717, 762125363937411132, [])
        print("Commands nuked")

    @Cog.listener()
    async def on_ready(self):
            if not self.bot.ready:
                self.bot.cogs_ready.ready_up("sync")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sync(bot))