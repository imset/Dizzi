from datetime import datetime
from discord import Embed
from discord.ext.commands import Cog
from discord.ext.commands import command

from ..db import db

class Log(Cog):
	def __init__(self, bot):
			self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
				self.bot.cogs_ready.ready_up("log")

	#doesn't work as intended
	
	@Cog.listener()
	async def on_user_update(self, before, after):

		#if username changes
		#if before.name != after.name:

		#the following can be used to store previous avatars after a switch.
		'''
		if before.avatar_url != after.avatar_url:
			#print("Avatar Change Trigger")
			db.execute("UPDATE avatarhistory SET Store4 = Store3 WHERE UserID = ?", after.id)
			#print("Success on 4->3")
			db.execute("UPDATE avatarhistory SET Store3 = Store2 WHERE UserID = ?", after.id)
			#print("Success on 3->2")
			db.execute("UPDATE avatarhistory SET Store2 = Store1 WHERE UserID = ?", after.id)
			#print("Success on 2->1")
			db.execute("UPDATE avatarhistory SET Store1 = Store0 WHERE UserID = ?", after.id)
			#print("Success on 1->0")
			db.execute("UPDATE avatarhistory SET Store0 = ?, Current = ? WHERE UserID = ?", str(before.avatar_url), str(after.avatar_url), after.id)
			#print("Success on final")
		'''
	
	'''
	@Cog.listener()
	async def on_member_update(self, before, after):
		
		#this code will log if someone changes their name. Log_channel must be defined
		
		if before.display_name != after.display_name:
			embed = Embed(title="Member update", description="Nickname change", color=after.color, timestamp = datetime.utcnow())
			fields = [("Before", before.display_name, False), ("After", after,display_name, False)]
			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.log_channel.send(embed=embed)


	'''
		
	'''	
	@Cog.listener()
	async def on_message_edit(self, before, after):
		if not after.author.bot:
			if before.content != after.content:

	@Cog.listener()
	async def on_message_delete(self, message):
		if not message.author.bot:
			#use message.content
			pass
	'''

def setup(bot):
		bot.add_cog(Log(bot))