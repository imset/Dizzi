from .db import db
import ast
import re
import emojis

class Dizzidb:
	def __init__(self, user, guild):
		#note: the user can be either a user or member object, and will be referred to as user here. This may change in the future.
		self.uid = user.id
		self.gid = guild.id
		self.dbid = f"{self.uid}.{self.gid}"

	def dblu(self, table, data, id):
		#database lookup
		data = db.field(f"SELECT {data} FROM {table} WHERE dbid = ?", id)
		return data

	def dbludict(self, table, data, id):
		#same as dblu but returns a dict
		data = db.field(f"SELECT {data} FROM {table} WHERE dbid = ?", id)
		try:
			datadict = ast.literal_eval(data)
		except:
			datadict = {}
		return datadict

	def dbluset(self, table, data, id):
		#same as dblu but returns an array, and actually I'm realizing now that this is the same code, but I'm keeping these seperate so that I can
		#keep naming conventions. this will be fixed in the dizzi slash command rewrite.
		data = db.field(f"SELECT {data} FROM {table} WHERE dbid = ?", id)
		try:
			dataset = ast.literal_eval(data)
		except:
			dataset = []
		return dataset

def dbsetup(guild):
	#this function will iterate through all the members of a guild and add them to all the tables of a db
	#first add the guild into the guildsettings table
	db.execute("INSERT or IGNORE INTO guildsettings (GuildID) VALUES (?)", guild.id)

	#iterate through member list and add them to tables
	memberlist = guild.members
	for member in memberlist:
		#ignore bots
		if not member.bot:
			userdb = Dizzidb(member, guild)
			db.execute("INSERT or IGNORE INTO emojicount (dbid) VALUES (?)", userdb.dbid)

def dbprefix(guild) -> str:
	prefix = db.field(f"SELECT prefix FROM guildsettings WHERE GuildID = ?", guild.id)
	return prefix

def dbemojiupdate(msg):
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

def dbreactupdate(msg):
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