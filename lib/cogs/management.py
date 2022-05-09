import discord
from discord import app_commands
from discord.ext.commands import Cog
from ..db import db
from ..dizzidb import Dizzidb, dbprefix


class Management(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    # group = app_commands.Group(name="parent", description="...")
    # # Above, we declare a command Group, in discord terms this is a parent command
    # # We define it within the class scope (not an instance scope) so we can use it as a decorator.
    # # This does have namespace caveats but i don't believe they're worth outlining in our needs.

    # @app_commands.command(name="top-command")
    # async def my_top_command(self, interaction: discord.Interaction) -> None:
    #     """ /top-command """
    #     await interaction.response.send_message("Hello from top level command!", ephemeral=True)
    

    # @group.command(name="sub-command") # we use the declared group to make a command.
    # async def my_sub_command(self, interaction: discord.Interaction) -> None:
    #     """ /parent sub-command """
    #     await interaction.response.send_message("Hello from the sub command!", ephemeral=True)

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("management")


async def setup(bot) -> None:
    await bot.add_cog(Management(bot))