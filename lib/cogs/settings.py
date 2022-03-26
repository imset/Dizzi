import re
import emojis
import math
from typing import Optional
import time


from discord.ext.commands import Cog
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions, is_owner, guild_only
from discord import TextChannel

from ..db import db
from ..dizzidb import Dizzidb, dbsetup, dbreactupdate, dbemojiupdate
from .reactions import has_emojis, has_reactions

DIZZICOLOR = 0x2c7c94

def emotefilter(message):

	#needs to be true for the messages that will be sent, and false for any others.
	botflag = not message.author.bot
	emoteflag = has_emojis(message)
	reactflag = has_reactions(message)
	filterflag = botflag and (emoteflag or reactflag)

	return filterflag

class Settings(Cog):
	
	def __init__(self, bot):
		self.bot = bot

	@command(name="welcomechannel",
			brief="Set a channel for Dizzi to greet people in.",
			usage="`*PREF*welcomechannel <channel>` - Sets the channel where Dizzi will welcome people. `<channel>` is a mentioned channel\nExample: `*PREF*welcomechannel #general`.")
	@has_permissions(manage_guild=True)
	@guild_only()
	async def change_welcomechannel(self, ctx, channel: TextChannel):
		"""Change the default welcome channel for Dizzi to greet people in. The channel must be properly mentioned with the # symbol."""
		db.execute("UPDATE guildsettings SET Welcome = ? WHERE GuildID = ?", str(channel.id), ctx.guild.id)
		await ctx.send(f"New Welcome Channel has been set.")


	@command(name="prefix",
			brief="Change the default prefix to use Dizzi commands",
			usage="`*PREF*prefix <new>` - changes the server prefix for Dizzi into the value for `<new>`.\nExample: `*PREF*prefix +`")
	@has_permissions(manage_guild=True)
	@guild_only()
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
	@guild_only()
	async def dbsetup(self, ctx):
		#this command will invoke a class to add all members of a server to a database
		message = await ctx.send(f"Setting up databases for {ctx.guild.name}...")
		try:
			dbsetup(ctx.guild)
		except:
			updated_member = await message.edit(content="Sorry, something went wrong.")
			return
		updated_member = await message.edit(content=f"Success! {ctx.guild.name} is all set up.")

	@command(name="emoteservhist",
			aliases=["esh"],
			hidden=True)
	@is_owner()
	@guild_only()
	async def emoteservhist(self, ctx, chnl: Optional[TextChannel]):
		#using this command will cause the bot to read through the entire server history and populate the emote history database
		#channels included with the command will be ignored
		progress = await ctx.send("Starting...")
		for channel in ctx.guild.text_channels:
			if channel == chnl:
				continue
			updated_member = await progress.edit(content=f"Analyzing last 1 million messages in {channel.name}...")
			messages = await channel.history(limit=1_000_000).flatten()
			updated_member = await progress.edit(content=f"Parsing recorded {channel.name} data for emojis...")
			for msg in messages:
				if msg.author.bot != True:
					if has_emojis(msg):

						userdb = Dizzidb(msg.author, msg.guild)

						#used to find custom emojis in the message and add them to the emojiset
						emojiset = re.findall(r'<a?:\w*:\d*>', msg.content)

						#it may be possible to optimize that regex so the below if/for loop, and the entire emoji library, isn't necessary

						#used to find default emojis in the message and add them to the emojiset
						if emojis.count(msg.content) > 0:
							for e in emojis.get(msg.content):
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

						#now reactions:

					if msg.reactions != []:
						for reaction in msg.reactions:
							#create userdb object
							userdb = Dizzidb(reaction.message.author, reaction.message.author.guild)
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

		updated_member = await progress.edit(content="Done!")

	@command(name="emotechannelhis",
			aliases=["ech"],
			hidden=True)
	@is_owner()
	@guild_only()
	async def emotechanhist(self, ctx, channel: TextChannel):
		#using this command will cause the bot to read through the channel history and populate the emote history database
		progress = await ctx.send("Starting...")
		updated_member = await progress.edit(content=f"Counting number of messages in {channel.name}...")
		#first, the bot will count the number of messages in the channel.
		count = 0
		async for _ in channel.history(limit=None):
			count += 1
		print(f"Message number for {channel.name}: {count}")

		updated_member = await progress.edit(content=f"Starting counting process...")
		time.sleep(2)
		firstbool = True
		epercent = 0
		beforemsg = []
		#while loop for the count
		while count > 0:
			#do in chunks of count/100
			if beforemsg != []:
				#for first iteration, no before value
				messages = await channel.history(limit=int(math.ceil(count/20))).flatten()
				firstbool = False
			else:
				messages = await channel.history(limit=int(math.ceil(count/20)), before=beforemsg).flatten()

			for msg in messages:
				if has_emojis(msg):
					dbemojiupdate(msg)
				if has_reactions(msg):
					dbreactupdate(msg)

			beforemsg = messages[-1]
			epercent += 5
			updated_member = await progress.edit(content=f"Completion for {channel.name} Emoji History: {epercent}\%")
			count -= (count/100)
		updated_member = await progress.edit(content="Done!")



		# await progress.edit(content=f"Analyzing last 50 thousand relevant messages in {channel.name}...")
		# messages = await channel.history(limit=50_000).filter(emotefilter).flatten()
		# await progress.edit(content=f"Recording emoji data for {channel.name}...")
		# for msg in messages:
		#     if has_emojis(msg):

		#         userdb = Dizzidb(msg.author, msg.guild)

		#         #used to find custom emojis in the message and add them to the emojiset
		#         emojiset = re.findall(r'<a?:\w*:\d*>', msg.content)

		#         #it may be possible to optimize that regex so the below if/for loop, and the entire emoji library, isn't necessary

		#         #used to find default emojis in the message and add them to the emojiset
		#         if emojis.count(msg.content) > 0:
		#             for e in emojis.get(msg.content):
		#                 emojiset.append(e)

		#         #if the dbid does not exist, create it
		#         if not db.dbexist("emojicount", "dbid", userdb.dbid):
		#             db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)

		#         #grabs the user's current emoji dictionary from the db
		#         uemojidict = userdb.dbludict("emojicount", "emojidict", userdb.dbid)

		#         #update the uemojidict and push that to the db
		#         if emojiset != []:
		#             for e in emojiset:
		#                 if e not in uemojidict:
		#                     uemojidict[e] = 1
		#                 else:
		#                     uemojidict[e] += 1
		#             db.execute("UPDATE emojicount SET emojidict = ? WHERE dbid = ?", str(uemojidict), userdb.dbid)

		#         #now reactions:

		#     if has_reactions(msg):
		#         for reaction in msg.reactions:
		#             #create userdb object
		#             userdb = Dizzidb(reaction.message.author, reaction.message.author.guild)
		#             #if a reaction can be formatted as the try, it's custom. Otherwise, it's a default emoji.
		#             try:
		#                 reactiondata = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
		#             except:
		#                 reactiondata = f"{reaction.emoji}"
					

		#             #if the dbid does not exist, create it
		#             if not db.dbexist("emojicount", "dbid", userdb.dbid):
		#                 db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)

		#             #get user's emoji dictionary
		#             uemojidict = userdb.dbludict("emojicount", "emojidict", userdb.dbid)
					
		#             #add the emoji to the dict if its not in, and if it is iterate it by 1
		#             if reactiondata not in uemojidict:
		#                 uemojidict[reactiondata] = 1
		#             else:
		#                 uemojidict[reactiondata] += 1
		#             db.execute("UPDATE emojicount SET emojidict = ? WHERE dbid = ?", str(uemojidict), userdb.dbid)
		# await progress.edit(content="Done!")

	# @command(name="testhist",
	# 		aliases=["th"],
	# 		hidden=True)
	# @is_owner()
	# async def testhist1(self, ctx, channel: TextChannel):

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("settings")
	
def setup(bot):
	bot.add_cog(Settings(bot))