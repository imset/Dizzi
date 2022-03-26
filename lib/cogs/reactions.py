import ast
import re
import emojis
from discord import Embed
from discord.ext.commands import Cog, command, guild_only
#from discord.ext.commands import command
from discord.ext.menus import MenuPages, ListPageSource
from discord.utils import get

from ..db import db
from ..dizzidb import Dizzidb


def has_emojis(message) -> bool:
	if emojis.count(message.content) > 0:
		return True
	else:
		ces = re.findall(r'<a?:\w*:\d*>', message.content)
		if ces != []:
			return True
		else:
			return False

def has_reactions(message) -> bool:
	if message.reactions != []:
		return True
	else:
		return False


class Reactions(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("reactions")

	#before Dizzi goes live for real, there should be a database to check against of servers that can have emote monitoring support

	@Cog.listener()
	async def on_message(self, message):
		#used to check a user's message for emojis, I should make it only fire if there's an emoji in it
		#ignore bots
		if (not message.author.bot) and (has_emojis(message)) and message.guild != None:
			#create a userdb
			userdb = Dizzidb(message.author, message.guild)

			#used to find custom emojis in the message and add them to the emojiset
			emojiset = re.findall(r'<a?:\w*:\d*>', message.content)

			#it may be possible to optimize that regex so the below if/for loop, and the entire emoji library, isn't necessary

			#used to find default emojis in the message and add them to the emojiset
			if emojis.count(message.content) > 0:
				for e in emojis.get(message.content):
					emojiset.append(e)

			#if the dbid does not exist, create it
			if not db.dbexist("emojicount", "dbid", userdb.dbid):
				db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)

			#grabs the user's current emoji dictionary from the db
			uemojidict = userdb.dbludict("emojicount", "emojidict", userdb.dbid)

			#update the uemojidict and push that to the db
			if emojiset != []:
				for e in emojiset:
					if e not in uemojidict:
						uemojidict[e] = 1
					else:
						uemojidict[e] += 1
				db.execute("UPDATE emojicount SET emojidict = ? WHERE dbid = ?", str(uemojidict), userdb.dbid)


	@Cog.listener()
	async def on_reaction_add(self, reaction, user):
		#monitor reactions for the emojidb
		#ignore bots
		if (not user.bot) and (not reaction.message.author.bot) and message.guild != None:
			#create userdb object
			userdb = Dizzidb(user, user.guild)
			#if a reaction can be formatted as the try, it's custom. Otherwise, it's a default emoji.
			try:
				reactiondata = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
			except:
				reactiondata = f"{reaction.emoji}"
			

			#if the dbid does not exist, create it
			if not db.dbexist("emojicount", "dbid", userdb.dbid):
				db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)

			#get user's emoji dictionary
			uemojidict = userdb.dbludict("emojicount", "emojidict", userdb.dbid)
			
			#add the emoji to the dict if its not in, and if it is iterate it by 1
			if reactiondata not in uemojidict:
				uemojidict[reactiondata] = 1
			else:
				uemojidict[reactiondata] += 1
			db.execute("UPDATE emojicount SET emojidict = ? WHERE dbid = ?", str(uemojidict), userdb.dbid)
		
	#the following is here to be uncommented in the future in case I ever decide I need them
	'''
	@Cog.listener()
	async def on_reaction_remove(self, reaction, user):
		pass	

	@Cog.listener()
	async def on_raw_reaction_add(self, reaction, user):
		print(f"[RAW] {payload.member.display_name} reacted with {payload.emoji.name}")

	@Cog.listener()
	async def on_raw_reaction_remove(self, reaction, user):
		pass
	'''

def setup(bot):
	bot.add_cog(Reactions(bot))