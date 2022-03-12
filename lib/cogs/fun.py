from aiohttp import request
import asyncio
from random import (
    choice, randint
)
from mediawiki import (
    MediaWiki, exceptions
)

from discord import (
    Member, Embed
)
from discord.ext.commands import (
    Cog, command, cooldown, BucketType, BadArgument
)

from discord.ext import tasks

from discord.errors import HTTPException

from datetime import date, datetime

import re

from ..db import db
from ..dizzidb import Dizzidb, dbprefix

DIZZICOLOR = 0x2c7c94

class Fun(Cog):
    """Test description for fun cog"""
    def __init__(self, bot):
        self.bot = bot
        
    @command(name="roll",
        aliases=["r"],
        brief="Roll some dice",
        usage="`*PREF*roll <die_string>` - Rolls dice. A valid `<die string>` is in the format XdY+Z or XdY-Z,"
        " where X is the number of dies to roll, Y is the value of the die, and Z is a bonus to apply at the end.\n"
        "Example: `*PREF*roll 2d20+5`")
    async def roll_dice(self, ctx, *, die_string: str):
        """Rolls a dice with optional bonus (+ or -)"""

        dnum, dval = (dice for dice in die_string.lower().split("d"))
        #this makes it so "d20" gets read as "1d20"
        try:
            dnum = int(dnum)
        except ValueError:
            dnum = 1
        
        #handle + or - operation into dbns. dbns is handled the same either way but the - causes it to be negative.
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
        
        #limit values
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
                await ctx.send(finalrollstr + " = " + str(rollsum) + "\n" + str(rollsum) + f" {operator} *" + 
                                str(abs(dbns)) + "* = __**" + str(rollsum + dbns) + "**__")
        else:
            if dbns == 0:
                await ctx.send(finalrollstr)
            else:
                await ctx.send(finalrollstr + f" {operator} *" + str(abs(dbns)) + "* = __**" + str(rollsum + dbns) + "**__")
            
    
    @command(name="slap",
            aliases=["hit"],
            brief="Slap someone for a reason",
            usage="`*PREF*slap <member> <reason>` - Slaps a `<member>` for a `<reason>`. The `<member>` should be properly"
            " pinged with @, the `<reason>` can be any text string to display after the slap. \nExample: `*PREF*slap @dizzi for no reason`")
    @cooldown(2, 5, BucketType.member)
    async def slap_member(self, ctx, member: Member, *, reason: str = ""):
        """Slap someone for any reason."""
        
        #the most weirdly comprehensive slap command ever, I want the reasons to make sense
        if reason != "":
            reasonlist = reason.split()
            #if the string starts with the word I, add "because" to the start
            if reasonlist[0].lower() == "i":
                reasonlist.insert(0, "because")
            #if the string starts with a verb, add "for" to the start
            elif reasonlist[0][-3:].lower() == "ing":
                reasonlist.insert(0, "for")
            elif reasonlist[0].lower() != "because" and reasonlist[0].lower() != "for" != "to":
                reasonlist.insert(0, "because")
            
            #word replacement loop
            for i, r in enumerate(reasonlist):
                if r.lower() == "cuz" or r.lower() == "bc":
                    reasonlist[i] = "because"
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
        
    @command(name="echo",
            aliases=["say"],
            brief="Repeat stuff, repeat stuff",
            usage="`*PREF*echo <message>` - Dizzi will repeat `<message>`\nExample: `*PREF*echo Hello World!`")
    async def echo_member(self, ctx, *, message):
        """Turn your own measly words into the words of the powerful Dizzi."""
        
        await ctx.message.delete()
        await ctx.send(message)
    
    @command(name="animalfact",
            aliases=["af"],
            brief="Get a fact about an animal",
            usage="`*PREF*animalfact <animal>` - gives a random animal fact and picture for a supported `<animal>`.\n"
            "Example: `*PREF*animalfact koala`")
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
        Powered by https://some-random-api.ml/
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
            
            
    @command(name="morelike",
            aliases=["ml"],
            brief="Get a scathing rhyme",
            usage="`*PREF*morelike <rhyme>` - gives you a word that rhymes with `<rhyme>`.\nExample: `*PREF*morelike Dog`")
    @cooldown(2, 10, BucketType.member)
    async def more_like(self, ctx, rhyme: str):
        """Get a scathing rhyme about a word of your choice. Useless? More like lupus.
        Powered by https://rhymebrain.com/"""

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
    
    @command(name="wikipedia",
            aliases=["wp"],
            brief="Search up an article on wikipedia",
            usage="`*PREF*wikipedia <page>` - gives a brief summary for the given wikipedia `<page>`. "
            "If an exact match is not found, the closest relevant one will be given.\nExample: `*PREF*wikipedia discord`")
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
            updated_member = await message.edit(content=f"I can't find anything on Wikipedia for {page.title()}. Sorry!")
            return
            
        embed = Embed(title=f"{pgtitle}", description=p.summarize(chars=350), color=DIZZICOLOR)
        embed.add_field(name="Read More", value=f"[Wikipedia](https://en.wikipedia.org/?curid={p.pageid})", inline=False)
        try:
            embed.set_thumbnail(url=p.logos[0])
        except:
            pass
            
        updated_member = await message.edit(content="", embed=embed)

    @command(name="alert",
            aliases=["tab","tabs"],
            brief="Keep tabs on someone and be alerted the next time they post something",
            usage="`*PREF*alert <user>` - Will alert you the next time a user posts something.\nExample: `*PREF*alert @hapaboba`")
    async def alert(self, ctx, member: Member):
        """Dizzi will ping you the next time a specific user sends a message."""
        if member.bot == True and member.name == "Dizzi":
            await ctx.send(f"I'm flattered but that doesn't really make sense, does it?")
            return
        elif member.bot == True:
            await ctx.send(f"Sorry, I don't pay attention to bots like {member.display_name}.")
            return
        #set the Dizzidb object as the mentioned member for lookup, also create normal userdb
        memberdb = Dizzidb(member, member.guild)
        userdb = Dizzidb(ctx.message.author, ctx.message.guild)
        #add them to the table if they're not there already
        db.execute("INSERT or IGNORE INTO alert (dbid) VALUES (?)", memberdb.dbid)
        #add the user's dbid into the alertdict
        alertset = memberdb.dbluset("alert", "alertset", memberdb.dbid)
        alertset.append(userdb.uid)
        db.execute("UPDATE alert SET alertset = ? WHERE dbid = ?", str(alertset), memberdb.dbid)
        await ctx.send(f"Alright, I'll keep track of {member.name} and let you know when they post in {ctx.guild.name} next.")

    @command(name="deflect",
            brief="Deflect a beam",
            usage="`*PREF*deflect` - It'll take more than that!\nExample: `*PREF*deflect`")
    async def alert(self, ctx):
        """Deflect a beam of energy so that it'll harmlessly hit a mountain in the background instead."""
        await ctx.send("https://i.imgur.com/MYI8EJh.gif")


    # @command(name="birthdayadd",
    #         aliases=["bdadd"],
    #         brief="Add a birthday to the birthdatabase",
    #         usage="`*PREF*birthdayadd <user>` -Adds a user to the birthday database so they'll be wished a happy birthday. Accepts dates formatted as MM/DD/YY, MM/DD/YYYY, or in a format such as February 27th, 1980. Birthday messages will be output to the welcome channel.\nExample: `*PREF*bdadd @dizzi 10/03`\n`*PREF*bdadd @dizzi Oct 03`")
    # async def bd_add(self, ctx, member: Member, *, day: str):
    #     """Add a user to Dizzi's birthday database"""
    #     if member.bot == True and member.name == "Dizzi":
    #         await ctx.send(f"I'm flattered, but I already know my birthday is October 3rd!")
    #         return
    #     elif member.bot == True:
    #         await ctx.send(f"Sorry, I don't wish birthdays to weird bots like {member.display_name}.")
    #         return

    #     #first check if string has '/' for the format xx/xx/xxxx
    #     if "/" in day:
    #         day.strip()
    #         daylist = day.split('/')
    #         if len(daylist[0]) == 1:
    #             monthval = f"0{daylist[0]}"
    #         else:
    #             monthval = daylist[0]
    #         if len(daylist[1]) == 1:
    #             dayval = f"0{daylist[1]}"
    #         else:
    #             dayval = daylist[1]
    #         if len(daylist[2]) == 1:
    #             yearval = f"0{daylist[2]}"
    #         else:
    #             yearval = daylist[2]
    #     else:
    #         #make everything lowercase
    #         day = day.lower()
    #         #now we need to search for a month, day, and year. Year should be 4 digits, month will be searched with a month code, day will be what's left
    #         #by default we assume the date is split by spaces here
    #         daylist = day.split(' ')
    #         for i in daylist:
    #             if "jan" in i:
    #                 monthval = "01"
    #                 break
    #             elif "feb" in i:
    #                 monthval = "02"
    #                 break
    #             elif "mar" in i:
    #                 monthval = "03"
    #                 break
    #             elif "apr" in i:
    #                 monthval = "04"
    #                 break
    #             elif "may" in i:
    #                 monthval = "05"
    #                 break
    #             elif "jun" in i:
    #                 monthval = "06"
    #                 break
    #             elif "jul" in i:
    #                 monthval = "07"
    #                 break
    #             elif "aug" in i:
    #                 monthval = "08"
    #                 break
    #             elif "sep" in i:
    #                 monthval = "09"
    #                 break
    #             elif "oct" in i:
    #                 monthval = "10"
    #                 break
    #             elif "nov" in i:
    #                 monthval = "11"
    #                 break
    #             elif "dec" in i:
    #                 monthval = "12"
    #                 break

    #         #now that we have the month, we need to disambiguate the year and the day. Using code from https://www.sanfoundry.com/python-program-count-number-digits/
    #         #to count digits - years should be 4 digits, day should be 1 or 2.

    #         #first remove all non-digits from each entry in daylist.
    #         i0 = re.sub('\D', '', daylist[0])
    #         i1 = re.sub('\D', '', daylist[1])
    #         i2 = re.sub('\D', '', daylist[2])
    #         daylisttemp = [i0, i1, i2]

    #         #now we need to iterate over each one and find the 4 digit year
    #         for i in daylisttemp:
    #             if i == '':
    #                 continue
    #             j = int(i)
    #             count=0
    #             while(j>0):
    #                 count=count+1
    #                 j=j//10
    #             if count == 4:
    #                 yearval = i
    #             else:
    #                 if len(i) == 1:
    #                     dayval = f"0{i}"
    #                 else:
    #                     dayval = i

    #     #shorten the year to the last two digits
    #     yearval = str(yearval)[-2:]

    #     finalmonthday = f"{monthval}/{dayval}"


    #     #set the Dizzidb object as the mentioned member for lookup, also create normal userdb
    #     memberdb = Dizzidb(member, member.guild)
    #     #add them to the database
    #     db.execute("INSERT or IGNORE INTO birthday (dbid) VALUES (?)", memberdb.dbid)
    #     #add the user's dbid into the alertdict
    #     db.execute("UPDATE birthday SET monthday = ? WHERE dbid = ?", finalmonthday, memberdb.dbid)
    #     db.execute("UPDATE birthday SET year = ? WHERE dbid = ?", yearval, memberdb.dbid)
    #     await ctx.send(f"Alright, I've added {finalmonthday}/{yearval} as {member.name}'s birthday. I'll be sure to wish them a happy birthday!")

    # @Cog.listener()
    # async def on_message(self, message):
    #     #used to check if a user is needed in the alert system
    #     #ignore bots
    #     if (not message.author.bot):
    #         #create a userdb
    #         userdb = Dizzidb(message.author, message.guild)

    #         if db.dbexist("alert", "dbid", userdb.dbid):
    #             ctx = await self.bot.get_context(message)
    #             alertset = userdb.dbluset("alert", "alertset", userdb.dbid)
    #             #now have the alertset, which should be set in the ;tabs command
    #             for u in alertset:
    #                 ping = await self.bot.fetch_user(u)
    #                 await ctx.send(f"{message.author.name} is online, {ping.mention}!")
    #             alertset = []
    #             db.execute("DELETE FROM alert WHERE dbid = ?", userdb.dbid)
    #         else:
    #             return

    # #birthday task loop
    # @tasks.loop(minutes = 60.0)
    # async def bdchk(self):
    #     #check if there's any birthdays today
    #     todaybds = db.column("SELECT dbid FROM birthday WHERE monthday = ?", str(date.today().strftime("%m/%d")))
    #     if todaybds == [] or todaybds == "":
    #         return
    #     else:
    #         for i in todaybds:
    #             wished = db.column("SELECT wished FROM birthday WHERE dbid = ?", i)
    #             if wished != 0 and datetime.now().hour >= 8:
    #                 splitset = i.split(".")
    #                 bduser = await self.bot.fetch_user(splitset[0])
    #                 bdguild = await self.bot.fetch_guild(splitset[1])
    #                 userdb = Dizzidb(bduser, bdguild)
    #                 welcomechannel = db.field("SELECT Welcome FROM guildsettings WHERE GuildID = ?", userdb.gid)
    #                 ping = await self.bot.fetch_user(userdb.uid)
    #                 print(f"Happy birthday dear {ping.display_name}")
    #                 channelpush = await self.bot.fetch_channel(int(welcomechannel))
    #                 await channelpush.send(f"**Today is {ping.mention}'s birthday**!")
    #                 wished = 1
    #                 db.execute("UPDATE birthday SET wished = ? WHERE dbid = ?", 1, i)

    # @tasks.loop(minutes = 60.0)
    # async def wishedreset(self):
    #     if datetime.now().hour < 8:
    #         db.execute("UPDATE birthday SET wished = ?", 0)

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
            
def setup(bot):
    bot.add_cog(Fun(bot))