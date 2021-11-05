from aiohttp import request
import asyncio
from mediawiki import (
    MediaWiki, exceptions
)

from discord import Embed, Member
from discord.errors import HTTPException
from discord.ext.commands import (
    Cog, command
)

#defines the bot's embed color
DIZZICOLOR = 0x2c7c94

#Currently this cog has no function

class Fightan(Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @command(name="strive",
            aliases=["ggs"],
            brief="This command does not yet function",
            hidden=True,
            enabled=False)
    async def strive_search(self, ctx, *, page: str):
        dl = MediaWiki(user_agent='py-Dizzi-Discord-Bot',url="http://www.dustloop.com/wiki/api.php")
        message = await ctx.send(f"Searching {page.title()} on Strive Dustloop")
        
        try:
            p = dl.page(title=f"GGST/{page}", preload=True)
            pgtitle = p.title
        except:
            p = dl.page(title=dl.search(f"GGST {page}"), preload=True)
            pgtitle = p.title + " (Closest Match to \"" + page.title() + "\")"
            
        embed = Embed(title=f"{pgtitle}", description=p.content.summarize(chars=300), color=DIZZICOLOR)
        embed.add_field(name="Read More", value=f"[Dustloop](https://www.dustloop.com/?curid={p.pageid})", inline=False)
        try:
            embed.set_thumbnail(url=p.logos[0])
        except:
            pass
        
        await message.edit(content="", embed=embed)

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fightan")
            
def setup(bot):
    bot.add_cog(Fightan(bot))