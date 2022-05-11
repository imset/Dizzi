from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.errors import HTTPException, Forbidden
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, DisabledCommand, CheckFailure
from discord.ext.commands import Context, is_owner, guild_only
from discord import Intents, Guild, channel, Object
from discord.ext import commands
from discord import Embed, File
from discord import Object as DiscordObject

from ..db import db
from ..dizzidb import Dizzidb


class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member):
        #create a Dizzidb object for the user who joined
        userdb = Dizzidb(member, member.guild)
        #find the welcome channel
        welcomechannel = db.field("SELECT Welcome FROM guildsettings WHERE GuildID = ?", userdb.gid)
        #insert the user into the relevant tables when they join
        db.execute("INSERT or IGNORE INTO exp (UserID) VALUES (?)", userdb.uid)
        db.execute("INSERT or IGNORE INTO avatarhistory (UserID) VALUES (?)", userdb.uid)
        db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)
        #welcome in the welcome channel
        if welcomechannel != "":
            await self.bot.get_channel(int(welcomechannel)).send(f"Welcome to **{member.guild.name}**, {member.mention}!")
    
    @Cog.listener()
    async def on_member_remove(self, member):
        #remove member from tables when they leave the server
        db.execute("DELETE FROM exp WHERE UserID = ?", member.id)

    @Cog.listener()
    async def on_ready(self):
            if not self.bot.ready:
                self.bot.cogs_ready.ready_up("welcome")

async def setup(bot):
    await bot.add_cog(Welcome(bot))