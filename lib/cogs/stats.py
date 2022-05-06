import ast
from typing import Optional

from discord import(
	Intents, Guild, channel, Embed,
	File, Member
)
from discord.errors import (
	HTTPException, Forbidden
)
from discord.ext.commands import (
	Cog, command, CommandNotFound, BadArgument, 
	MissingRequiredArgument, CommandOnCooldown, DisabledCommand, CheckFailure,
	Context, guild_only
)	
from discord.ext.menus import (
	MenuPages, ListPageSource
)
from collections import Counter

from ..db import db
from ..dizzidb import Dizzidb

DIZZICOLOR = 0x2c7c94

#creates the menu for emoji stats
class EmojiMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx
		#immediately sort the all the data in the list by the second index
		data = sorted(data, key=lambda x:(x[1]), reverse=True)
		super().__init__(data, per_page=5)

	async def write_page(self, menu, fields=[]):
		#offset for footers and rankings
		offset = (menu.current_page*self.per_page) + 1
		len_data = len(self.entries)

		#the member is always given redundantly at index 2 of the list
		member = fields[0][2]

		#create embed
		embed = Embed(title=f"{member.name}'s Top Emojis for: {member.guild.name}", description="...", color=DIZZICOLOR)        
		embed.set_thumbnail(url=member.avatar)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} Emojis.")

		#i is used for the ranking value of emojis
		i = offset
		for key, value, member in fields:
			#generates the fields with the emoji and its ranking
			embed.add_field(name=f"**————————————————**\n#{i}", value=f"{key} x{value}", inline=False)
			i += 1

		return embed

	async def format_page(self, menu, entries):
		fields = []
		
		for key, value, member in entries:
			#creates the field list that will be used in write_page to add fields
			fields.append([key, value, member])

		#sorts again (seems redundant but stuff breaks without this for some reason)
		fields = sorted(fields, key=lambda x: (x[1]), reverse=True)

		return await self.write_page(menu, fields)

#server emoji menu, used for server command
class ServerEmojiMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx
		#immediately sort the all the data in the list by the second index
		data = sorted(data, key=lambda x:(x[1]), reverse=True)
		super().__init__(data, per_page=5)

	async def write_page(self, menu, fields=[]):
		#offset for footers and rankings
		offset = (menu.current_page*self.per_page) + 1
		len_data = len(self.entries)

		#the guild is always given redundantly at index 2 of the list
		guild = fields[0][2]

		#create embed
		embed = Embed(title=f"{guild.name}'s Top Emojis", description="...", color=DIZZICOLOR)        
		if guild.icon != None:
			embed.set_thumbnail(url=guild.icon)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} Emojis.")

		#i is used for the ranking value of emojis
		i = offset
		for key, value, guild in fields:
			#generates the fields with the emoji and its ranking
			embed.add_field(name=f"**————————————————**\n#{i}", value=f"{key} x{value}", inline=False)
			i += 1

		return embed

	async def format_page(self, menu, entries):
		fields = []
		
		for key, value, member in entries:
			#creates the field list that will be used in write_page to add fields
			fields.append([key, value, member])

		#sorts again (seems redundant but stuff breaks without this for some reason)
		fields = sorted(fields, key=lambda x: (x[1]), reverse=True)

		return await self.write_page(menu, fields)



class Stats(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
			if not self.bot.ready:
				self.bot.cogs_ready.ready_up("stats")

	@command(name="emojihistory",
			aliases=["emotehistory", "eh"],
			brief="See a user's favorite emojis",
			usage="`*PREF*emojihistory <member>` - Get a list of `<member>`'s favorite emojis on the current server. If `<member>` is not given, it defaults to your own list.\nExample: `*PREF*emojihistory @jeff`")
	@guild_only()
	async def emoji_history(self, ctx, member: Optional[Member]):
		"""Find out what your friend's favorite emojis are. Data is based off both message emojis and reaction emojis.
		Record keeping began on 11/1/2021"""

		#set the member to the person who called the command by default
		if member == None:
			member = ctx.message.author
		elif member.bot == True and member.name == "Dizzi":
			await ctx.send(f"I'm far too busy to keep track of my own emojis!")
			return
		elif member.bot == True:
			await ctx.send(f"Sorry, I don't pay attention to bots like {member.display_name}.")
			return

		#create the userdb object
		userdb = Dizzidb(member, member.guild)

		#try to get the emoji dictionary for the user, if not the user hasn't used emojis
		uemojidict = userdb.dbludict("emojicount", "emojidict", userdb.dbid)
		if uemojidict == {}:
			await ctx.send("User hasn't used emotes on this server")
			return

		#emojilist is a list of lists that will be passed into the menu
		emojilist = []
		for key, value in uemojidict.items():
			# this is hilariously inefficient but I can't figure out a better way to make this happen than by throwing the member in with every key/value
			emojilist.append([key, value, member])

		#start menu
		menu = MenuPages(source=EmojiMenu(ctx, emojilist))
		await menu.start(ctx)

	@command(name="serveremojihistory",
			aliases=["serveremotehistory", "seh"],
			brief="See the server's favorite emojis",
			usage="`*PREF*serveremojihistory` - Get a list of the server's favorite emojis. \nExample: `*PREF*seh`")
	@guild_only()
	async def server_emoji_history(self, ctx):

		fullemoji = []
		
		#populate keys list
		for member in ctx.guild.members:
			if member.bot != True:
				m = Dizzidb(member, ctx.guild)
				d = m.dbludict("emojicount", "emojidict", m.dbid)
				fullemoji.append(d)

		#fullemoji is now a list of every user followed by their emojidict. Now to iterate over them and combine them.

		serverdict = {}

		#thanks to https://www.kite.com/python/answers/how-to-add-values-from-two-dictionaries-in-python
		for val in fullemoji:
			sd_counter = Counter(serverdict)
			val_counter = Counter(val)

			add_dict = sd_counter + val_counter
			serverdict = dict(add_dict)

		emojilist = []
		for key, value in serverdict.items():
			# this is hilariously inefficient but I can't figure out a better way to make this happen than by throwing the member in with every key/value
			emojilist.append([key, value, ctx.guild])

		#start menu
		menu = MenuPages(source=ServerEmojiMenu(ctx, emojilist))
		await menu.start(ctx)


	
async def setup(bot):
	await bot.add_cog(Stats(bot))