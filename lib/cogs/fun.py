from discord.ext.commands import Cog
from discord.ext.commands import command
from random import choice, randint
from discord import Member
from discord.errors import HTTPException
from aiohttp import request
import asyncio
from discord import Embed
from mediawiki import MediaWiki
from mediawiki import exceptions

DIZZICOLOR = 0x2c7c94
wikipedia = MediaWiki(user_agent='py-Dizzi-Discord-Bot')


class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot 
        
    @command(name="roll", aliases=["r"])
    async def roll_dice(self, ctx, *, die_string: str):      
        dnum, dval = (dice for dice in die_string.lower().split("d"))
        dnum = int(dnum)
        
        if "+" in dval:
            dval, dbns = (int(dice) for dice in dval.lower().split("+"))
        else:
            dbns = 0
            dval = int(dval)
            
        if dnum > 100 or dval > 100 or dbns > 100:
            await ctx.send("Error: please limit sides/rolls/bonus to 100 max.")
            return
            
        rolls = [randint(1, dval) for i in range(dnum)]
        rollstr = [str(r) for r in rolls]
        i = 0
        
        while i < len(rolls):
            if rolls[i] == dval:
                rollstr[i] = "**" + rollstr[i] + "**"
            else:
                #rolls[i] = str(rolls[i])
                pass
            i += 1
            
        finalrollstr = " + ".join(rollstr)
        rollsum = sum(rolls)
        
        if dbns == 0:
            await ctx.send(finalrollstr + " = " + str(rollsum))
        else:
            await ctx.send(finalrollstr + " = " + str(rollsum) + " + *" + str(dbns) + "* = __**" + str(rollsum + dbns) + "**__")
            
          
    @roll_dice.error
    async def roll_dice_error(self, ctx, exc):
        if isinstance(exc.original, HTTPException):
            await ctx.send("Result too large, try a lower number")
    
    @command(name="slap", aliases=["hit"])
    async def slap_member(self, ctx, member: Member, *, reason: str = "for no reason"):
        await ctx.send(f"{ctx.author.display_name} slapped {member.mention} {reason}.")
        
    @slap_member.error
    async def slap_member_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            await ctx.send("I can't find that member.")
        
    @command(name="echo", aliases=["say"])
    async def echo_member(self, ctx, *, message):
        await ctx.message.delete()
        await ctx.send(message)
    
    @command(name="animalfact")
    async def animal_fact(self, ctx, animal: str):
        if animal.lower() in ("dog", "cat", "panda", "fox", "koala", "bird", "raccoon", "kangaroo"):
            URL = f"https://some-random-api.ml/animal/{animal.lower()}"
            
            async with request("GET", URL, headers={}) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = Embed(title=f"{animal.title()} fact", description=data["fact"], color=DIZZICOLOR)
                    embed.set_thumbnail(url=data["image"])
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"API returned a {response.status} status.")
        else:
            await ctx.send("No facts are available for that animal. Available facts:\nDog, Cat, Panda, Fox, Koala, Bird, Raccoon, Kangaroo")
            
    '''
    @command(name="pokedex", aliases=["dex"])
    async def pokedex_member(self, ctx, mon: str):
        URL = f"https://pokeapi.co/api/v2/pokemon/{mon}"

        async with request("GET", URL, headers={}) as response:
            if response.status == 200:
                await ctx.send("Pokemon found")
            else:
                await ctx.send("Pokemon not found")
    '''
    
    @command(name="wikipedia", aliases=["wp"])
    async def wikipedia_member(self, ctx, *, page: str):
        
        message = await ctx.send(f"Searching {page.title()} on Wikipedia")
        
        try:
            p = wikipedia.page(page)
            pgtitle = p.title
        except exceptions.DisambiguationError as e:
            #print("Exception.__class__: {0}".format(e.__class__))
            p = wikipedia.page(wikipedia.search(page)[1])
            pgtitle = p.title + " (Closest Match to \"" + page.title() + "\")"
        except exceptions.PageError as e:
            await message.edit(content=f"I can't find anything on Wikipedia for {page.title()}. Sorry!")
            return
            
        embed = Embed(title=f"{pgtitle}", description=p.summarize(chars=350), color=DIZZICOLOR)
        embed.add_field(name="Read More", value=f"[Wikipedia](https://en.wikipedia.org/?curid={p.pageid})", inline=False)
        try:
            embed.set_thumbnail(url=p.logos[0])
        except:
            pass
            
        await message.edit(content="", embed=embed)
        

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
            
def setup(bot):
    bot.add_cog(Fun(bot))