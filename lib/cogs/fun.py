from discord.ext.commands import Cog
from discord.ext.commands import command, cooldown, BucketType, BadArgument
from random import choice, randint
from discord.errors import HTTPException
from aiohttp import request
import asyncio
from discord import Member, Embed
from mediawiki import MediaWiki
from mediawiki import exceptions

from ..db import db

DIZZICOLOR = 0x2c7c94


class Fun(Cog):
    """Test description for fun cog"""
    def __init__(self, bot):
        self.bot = bot 
        
    @command(name="roll", aliases=["r"], brief="Roll some dice", usage="`roll <die_string>` - Rolls dice. A valid `die string` is in the format XdY+Z or XdY-Z, where X is the number of dies to roll, Y is the value of the die, and Z is a bonus to apply at the end.\nExample: `roll 2d20+5`")
    async def roll_dice(self, ctx, *, die_string: str):
        """Rolls a dice with optional bonus (+ or -)"""
        #todo: minus
        dnum, dval = (dice for dice in die_string.lower().split("d"))
        dnum = int(dnum)
        
        if "+" in dval:
            dval, dbns = (int(dice) for dice in dval.lower().split("+"))
            operator = "+"
        elif "-" in dval:
            dval, dbns = (int(dice) for dice in dval.lower().split("-"))
            dbns = int(0-dbns)
            operator = "-"
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
        
        if int(dnum) != 1:
            if dbns == 0:
                await ctx.send(finalrollstr + " = " + str(rollsum))
            else:
                await ctx.send(finalrollstr + " = " + str(rollsum) + "\n" + str(rollsum) + f" {operator} *" + str(abs(dbns)) + "* = __**" + str(rollsum + dbns) + "**__")
        else:
            if dbns == 0:
                await ctx.send(finalrollstr)
            else:
                await ctx.send(finalrollstr + f" {operator} *" + str(abs(dbns)) + "* = __**" + str(rollsum + dbns) + "**__")
            
    
    @command(name="slap", 
            aliases=["hit"], 
            brief="Slap someone for a reason", 
            usage="`slap <member> <reason>` - Slaps a `member` for a `reason`. The `member` must be properly pinged with @, the `reason` can be any text string to display after the slap. \nExample: `slap @dizzi for no reason`")
    @cooldown(2, 5, BucketType.member)
    async def slap_member(self, ctx, member: Member, *, reason: str = ""):
        """Slap someone for any reason."""
        #the most weirdly comprehensive slap command ever, I want the reasons to make sense
        if reason != "":
            reasonlist = reason.split()
            # if the string starts with the word I, add "because" to the start
            if reasonlist[0].lower() == "i":
                reasonlist.insert(0, "because")
            # if the string starts with a verb, add "for" to the start
            elif reasonlist[0][-3:].lower() == "ing":
                reasonlist.insert(0, "for")
            elif reasonlist[0].lower() != "because" and reasonlist[0].lower() != "for":
                reasonlist.insert(0, "because")
            
            # word replacement loop
            for i, r in enumerate(reasonlist):
                # replaces shorthand for because
                if r.lower() == "cuz" or r.lower() == "bc":
                    reasonlist[i] = "because"
                # replaces "I" with "they"
                elif r.lower() == "i":
                    reasonlist[i] = "they"

                elif r.lower() == "dizzi":
                    reasonlist[i] = "me"
                elif r.lower() == "me":
                    reasonlist[i] = "them"
                elif r.lower() == "myself":
                    reasonlist[i] = "themself"
                elif r.lower() == "my":
                    reasonlist[i] = "their"
                    
            # uppercase loop if relevant
            if reason.upper() == reason:
                for i, r in enumerate(reasonlist):
                    reasonlist[i] = r.upper()
            reason = " ".join(reasonlist)
        else:
            reason = "for no reason"
        await ctx.send(f"{ctx.author.display_name} slapped {member.mention} {reason}.")
        
    @slap_member.error
    async def slap_member_error(self, ctx, exc):
        if isinstance(exc, BadArgument):
            await ctx.send("I can't find that user. Make sure you ping them!")
        
    @command(name="echo", aliases=["say"], brief="Repeat stuff, repeat stuff", usage="`echo <message>` - Dizzi will repeat `message`\nExample: `echo Hello World!`")
    async def echo_member(self, ctx, *, message):
        """Turn your own measly words into the words of the powerful Dizzi."""
        
        await ctx.message.delete()
        await ctx.send(message)
    
    @command(name="animalfact", brief="Get a fact about an animal", usage="`animalfact <animal>` - gives a random animal fact and picture for a supported `animal`.\nExample: `animalfact koala`")
    async def animal_fact(self, ctx, animal: str):
        """Get a random fact and picture for the supported animals 
        Currently supported animals:
            `Dog`
            `Cat`
            `Panda`
            `Fox`
            `Koala`
            `Bird`
            `Raccoon`
            `Kangaroo`
            """
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
            await ctx.send("No facts are available for that animal. Use help animalfact to get a list of supported animals.")
            
            
    @command(name="morelike", brief="Get a scathing rhyme", usage="`morelike <rhyme>` - gives you a word that rhymes with `rhyme`.\nExample: `morelike Dog`")
    @cooldown(2, 10, BucketType.member)
    async def more_like(self, ctx, rhyme: str):
        """Get a scathing rhyme about a word of your choice. Useless? More like lupus."""
        #remove whitespace
        rhyme.replace(" ", "")
        URL = f"https://rhymebrain.com/talk?function=getRhymes&word={rhyme.lower()}"
        async with request("GET", URL, headers={}) as response:
            if response.status == 200:
                data = await response.json()
                
                #first get the best possible rhyme score
                targetscore = int(data[0]["score"])
                rhymelist = []
                
                # now create a list of rhymes that are within 20 of that score and do not have "a" flag / no flags
                for d in data:
                    if (int(d["score"]) >= (targetscore-20)) and ("a" not in d["flags"]) and (d["flags"] != None):
                        rhymelist.append(d["word"])
                    elif (int(d["score"]) < (targetscore-20)):
                        break
                        
                # search range is between 0 and i-1
                
                await ctx.send(f"{rhyme.title()}? More like **{choice(rhymelist)}**!")
            else:
                print(f"API returned a {response.status} status.")
            
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
    
    @command(name="wikipedia", aliases=["wp"], brief="Search up an article on wikipedia", usage="`wikipedia <page>` - gives a brief summary for the given wikipedia `page`. If an exact match is not found, the closest relevant one will be given.\nExample: `wikipedia discord`")
    async def wikipedia_member(self, ctx, *, page: str):
        """Too lazy to use google? Ask Dizzi to look up wikipedia articles and get a brief summary + link"""
        wikipedia = MediaWiki(user_agent='py-Dizzi-Discord-Bot')
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