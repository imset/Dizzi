from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.errors import HTTPException, Forbidden
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, DisabledCommand, CheckFailure
from discord.ext.commands import Context
from discord import Intents, Guild, channel
from discord.ext import commands
from discord import Embed, File, Member
import ast
from discord.ext.menus import MenuPages, ListPageSource
from typing import Optional



from ..db import db

DIZZICOLOR = 0x2c7c94

class HelpMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx
		data = sorted(data, key=lambda x:(x[1]), reverse=True)
		super().__init__(data, per_page=5)

	async def write_page(self, menu, fields=[]):
		offset = (menu.current_page*self.per_page) + 1
		len_data = len(self.entries)

		member = fields[0][2]

		embed = Embed(title=f"{member.name}'s Top Emojis for {member.guild.name}", description="(Began Recording 11/1/2021)", color=DIZZICOLOR)        
		embed.set_thumbnail(url=member.avatar_url)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} Emojis.")
		i = offset
		for key, value, member in fields:
			#generate cog name headers and create fields. Within Dizzi's help documents, cogs are referred to as groups.
			embed.add_field(name=f"**————————————————**\n#{i} - {key}", value=f"Used {value} Times", inline=False)
			#print(f"{key} | {value}")
			i += 1

		return embed

	async def format_page(self, menu, entries):
		fields = []
		
		#append the member
		#fields.append(entries[0])

		for key, value, member in entries:
			#creates the field list that will be used in write_page to add fields
			fields.append([key, value, member])

		#sort fields list by value
		fields = sorted(fields, key=lambda x: (x[1]), reverse=True)
		#print(fields)

		return await self.write_page(menu, fields)


class Stats(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
			if not self.bot.ready:
				self.bot.cogs_ready.ready_up("stats")

	@command(name="emojihistory", aliases=["emotehistory", "eh"], brief="See a user's favorite emojis", usage="`emojihistory <member>` - Get a list of `<member>`'s favorite emojis on the current server. If `<member>` is not given, it defaults to your own list.\nExample: `emojihistory @jeff`")
	async def emoji_history(self, ctx, member: Optional[Member]):
		"""Find out what your friend's favorite emojis are. Data is based off both message emojis and reaction emojis.
		Record keeping began on 11/1/2021"""

		if member == None:
			member = ctx.message.author

		uguild = f"{member.id}.{member.guild.id}"
		try:
			userredict = ast.literal_eval(db.field("SELECT reactiondict FROM reactioncounter WHERE UserGuildID = ?", uguild))
		except ValueError:
			await ctx.send("User hasn't used emotes on this server")
			return
		#userredict = sorted(userredict, key = userredict.get)
		emojilist = []
		#emojilist is a list of lists that has keys and values
		for key, value in userredict.items():
			# this is hilariously inefficient but I can't figure out a better way to make this happen than by throwing the member in with every key/value
			emojilist.append([key, value, member])

		#emojilist.sort(key=lambda x:[1])

		menu = MenuPages(source=HelpMenu(ctx, emojilist), delete_message_after=True, timeout=60.0)
		await menu.start(ctx)



	
def setup(bot):
	bot.add_cog(Stats(bot))