from .db import db
import ast

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
		datadict = ast.literal_eval(data)
		return datadict

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