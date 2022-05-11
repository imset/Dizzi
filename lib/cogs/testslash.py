import asyncio
import discord

from discord import (
    Member, Embed, app_commands, Interaction, app_commands, Object, HTTPException, Message
)

from discord.ext.commands import (
    GroupCog, Cog, command, hybrid_command, cooldown, BucketType, BadArgument, guild_only, group, hybrid_group, is_owner, guild_only, Context, Greedy
)

from discord.ext import commands
class Testslash(Cog):
            
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        #hacky solution to add context menus through cogs
        self.ctx_menu = app_commands.ContextMenu(name="React", callback=self.reactioncmnu, guild_ids=[762125363937411132],)
        self.bot.tree.add_command(self.ctx_menu)

    #hybrid command functions

    #context menu commands
    async def reactioncmnu(self, interaction:Interaction, message:Message):
        await interaction.response.send_message('Very cool message!')

    #cleanup context menu on cog unload  
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