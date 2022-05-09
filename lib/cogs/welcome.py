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
	async def on_ready(self):
			if not self.bot.ready:
				self.bot.cogs_ready.ready_up("welcome")

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

	@command(name="testsync",
	        aliases=["ts"],
	        hidden=True)
	@is_owner()
	@guild_only()
	async def testsync(self, ctx):
	    try:
	        # self.bot.tree.clear_commands(guild=DiscordObject(id=473089232798220288))
	        # await self.bot.tree.sync(guild=DiscordObject(id=473089232798220288))
	        #self.bot.tree.clear_commands()
	        await self.bot.tree.sync(guild=DiscordObject(762125363937411132))
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
	    try:
	        # self.bot.tree.clear_commands(guild=DiscordObject(id=473089232798220288))
	        # await self.bot.tree.sync(guild=DiscordObject(id=473089232798220288))
	        #self.bot.tree.clear_commands()
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
		await self.bot.http.bulk_upsert_global_commands(588587478970269717, [])
		await self.bot.http.bulk_upsert_guild_commands(588587478970269717, 762125363937411132, [])
		print("Commands nuked")

	    #await ctx.send("Initiating global sync. If nothing changes in an hour, please panic.")


	# @command(name="troubleshootslash")
	# @is_owner()
	# async def troubleshootslash(self, ctx):
	# 	for command in commands:
	# 		if not (1 < len(command.Describe) < 100):
	# 			print(command)
	# 	await ctx.send("pushed to console")

async def setup(bot):
	await bot.add_cog(Welcome(bot))