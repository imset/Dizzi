from discord.ext.commands import Cog
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions, is_owner
from discord import TextChannel

from ..db import db
from ..dizzidb import Dizzidb, dbsetup

DIZZICOLOR = 0x2c7c94


class Settings(Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @command(name="welcomechannel",
            brief="Set a channel for Dizzi to greet people in.",
            usage="`*PREF*welcomechannel <channel>` - Sets the channel where Dizzi will welcome people. `<channel>` is a mentioned channel\nExample: `*PREF*welcomechannel #general`.")
    @has_permissions(manage_guild=True)
    async def change_welcomechannel(self, ctx, channel: TextChannel):
        """Change the default welcome channel for Dizzi to greet people in. The channel must be properly mentioned with the # symbol."""
        db.execute("UPDATE guildsettings SET Welcome = ? WHERE GuildID = ?", str(channel.id), ctx.guild.id)
        await ctx.send(f"New Welcome Channel has been set.")


    @command(name="prefix",
            brief="Change the default prefix to use Dizzi commands",
            usage="`*PREF*prefix <new>` - changes the server prefix for Dizzi into the value for `<new>`.\nExample: `*PREF*prefix +`")
    @has_permissions(manage_guild=True)
    async def change_prefix(self, ctx, new: str):
        """Change the default prefix that Dizzi will pay attention to. Be careful not to choose one already taken by another bot!"""
        if len(new) > 5:
            await ctx.send("Your prefix is too powerful. Try one less than 5 characters.")
        else:
            db.execute("UPDATE guildsettings SET Prefix = ? WHERE GuildID = ?", new, ctx.guild.id)
            await ctx.send(f"Prefix set to {new}.")

    @command(name="dbsetup",
            hidden=True)
    @is_owner()
    async def dbsetup(self, ctx):
        #this command will invoke a class to add all members of a server to a database
        message = await ctx.send(f"Setting up databases for {ctx.guild.name}...")
        try:
            dbsetup(ctx.guild)
        except:
            await message.edit(content="Sorry, something went wrong.")
            return
        await message.edit(content=f"Success! {ctx.guild.name} is all set up.")
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("settings")
    
def setup(bot):
    bot.add_cog(Settings(bot))