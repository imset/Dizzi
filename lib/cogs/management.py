import discord
from discord import app_commands
from discord.ext.commands import Cog
from ..db import db
from ..dizzidb import Dizzidb, dbprefix


class Management(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    #todo: management options

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("management")


async def setup(bot) -> None:
    await bot.add_cog(Management(bot))