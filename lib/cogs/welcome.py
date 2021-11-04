from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.errors import HTTPException, Forbidden
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, DisabledCommand, CheckFailure
from discord.ext.commands import Context
from discord import Intents, Guild, channel
from discord.ext import commands
from discord import Embed, File

from ..db import db

class Welcome(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
			if not self.bot.ready:
				self.bot.cogs_ready.ready_up("welcome")

	@Cog.listener()
	async def on_member_join(self, member):
		#userandguildlist = [str(member.id), str(member.guild.id)]
		uguild = f"{member.id}.{member.guild.id}"
		welcomechannel = db.field("SELECT Welcome FROM guildsettings WHERE GuildID = ?", member.guild.id)
		db.execute("INSERT or IGNORE INTO exp (UserID) VALUES (?)", member.id)
		db.execute("INSERT or IGNORE INTO avatarhistory (UserID) VALUES (?)", member.id)
		db.execute("INSERT or IGNORE INTO reactioncounter (UserGuildID) VALUES (?)", uguild)
		if welcomechannel != "":
			await self.bot.get_channel(int(welcomechannel)).send(f"Welcome to **{member.guild.name}**, {member.mention}!")

	@Cog.listener()
	async def on_member_remove(self, member):
		db.execute("DELETE FROM exp WHERE UserID = ?", member.id)


def setup(bot):
	bot.add_cog(Welcome(bot))