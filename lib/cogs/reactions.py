from discord.ext.commands import Cog
from discord import Embed
from discord.ext.commands import Cog
from discord.ext.commands import command
import ast
import re
import emojis
from discord.ext.menus import MenuPages, ListPageSource
from discord.utils import get

from ..db import db

class HelpMenu(ListPageSource):
    def __init__(self, ctx, data, member):
        self.ctx = ctx
        
        #cogdict = {}
        
        
        super().__init__(data, per_page=5)
        
    async def write_page(self, menu, fields=[]):
        offset = (menu.current_page*self.per_page) + 1
        len_data = len(self.entries)
        
        embed = Embed(title="Dizzi's Command Help", description="What can I help you with? \n(Hint: use help <command> for more info about a specific command, or help <group> to get info about a group of commands)",color=DIZZICOLOR)
        
        embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")
        cogname = ""
        for brief, value, cog, hidden, name, enabled in fields:
            #generate cog name headers and create fields. Within Dizzi's help documents, cogs are referred to as groups.
            
            if hidden != True and enabled != False:
                if cog != cogname:
                    cogname = cog
                    embed.add_field(name="**————————————————**", value = f"**{str(cogname).title()} Group:\n————————————————**", inline=False)
                embed.add_field(name=brief, value=value, inline=False)
            else:
                continue
            
        return embed
        
    async def format_page(self, menu, entries):
        fields = []
        
        for entry in entries:
            #creates the field list that will be used in write_page to add fields
            fields.append((entry.brief or "No description", syntax(entry), entry.cog_name, entry.hidden, entry.name, entry.enabled))
            
        #sort fields list by cog_name and syntax(entry)
        fields = sorted(fields, key=lambda x: (x[2], x[4]))
        #print(fields)
        
        return await self.write_page(menu, fields)

class Reactions(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("reactions")

	#going to try to do this like this and see if it works
	@Cog.listener()
	async def on_message(self, message):
		#before Dizzi goes live, there should be a database to check against of servers that can have emote monitoring support
		if (not message.author.bot):
			#creates the uguild string, used for the database
			uguild = f"{message.author.id}.{message.guild.id}"
			#creates a set filled with all emoji data
			emojiset = re.findall(r'<:\w*:\d*>', message.content)
			if emojis.count(message.content) > 0:
				for e in emojis.get(message.content):
					emojiset.append(e)
			userredict = ast.literal_eval(db.field("SELECT reactiondict FROM reactioncounter WHERE UserGuildID = ?", uguild))
			#db.emotedict(message.author.id, message.guild.id)
			if emojiset != []:
				for e in emojiset:
					if e not in userredict:
						userredict[e] = 1
					else:
						userredict[e] += 1
				db.execute("UPDATE reactioncounter SET reactiondict = ? WHERE UserGuildID = ?", str(userredict), uguild)


	@Cog.listener()
	async def on_reaction_add(self, reaction, user):
		
		if not user.bot and not reaction.message.author.bot:
			try:
				reactiondata = f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
			except:
				reactiondata = f"{reaction.emoji}"
			
			uguild = f"{user.id}.{user.guild.id}"
			userredict = ast.literal_eval(db.field("SELECT reactiondict FROM reactioncounter WHERE UserGuildID = ?", uguild))
			
			#userredict = emotedict(user.id, user.guild.id)
			if reactiondata not in userredict:
				userredict[reactiondata] = 1
			else:
				userredict[reactiondata] += 1
			db.execute("UPDATE reactioncounter SET reactiondict = ? WHERE UserGuildID = ?", str(userredict), uguild)
		'''
		elif user.bot:
			print("bot made a reaction")
		elif reaction.message.author.bot:
			print(f"{user.display_name} reacted to a bot")
		'''
		
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