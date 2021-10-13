from discord.ext.commands import Cog
from discord.ext.commands import command
from discord import Embed
#for timezone handling
from datetime import date
from datetime import datetime, timedelta
import pytz
from pytz import timezone
from random import choice, randint
from discord import Member
from discord.errors import HTTPException
from aiohttp import request
import asyncio
from mediawiki import MediaWiki
from mediawiki import exceptions

#defines the bot's embed color
DIZZICOLOR = 0x2c7c94
dl = MediaWiki(user_agent='py-Dizzi-Discord-Bot',url="http://www.dustloop.com/wiki/api.php")


class Fightan(Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @command(name="strive", aliases=["ggs"])
    async def strive_search(self, ctx, *, page: str):
        message = await ctx.send(f"Searching {page.title()} on Strive Dustloop")
        
        try:
            p = dl.page("GGST/" + page)
            pgtitle = p.title
        except:
            p = dl.page(dl.search("GGST" + page))
            pgtitle = p.title + " (Closest Match to \"" + page.title() + "\")"
            
        embed = Embed(title=f"{pgtitle}", description=p.summarize(chars=300), color=DIZZICOLOR)
        embed.add_field(name="Read More", value=f"[Dustloop](https://www.dustloop.com/?curid={p.pageid})", inline=False)
        try:
            embed.set_thumbnail(url=p.logos[0])
        except:
            pass
        print(p.wikitext)
        
        await message.edit(content="", embed=embed)

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fightan")
            
def setup(bot):
    bot.add_cog(Fightan(bot))