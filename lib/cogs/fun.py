import aiohttp
import sys
import re
import asyncio
import discord
import enum
import io
import functools
import replicate
from typing import Literal, Optional
from random import (
    choice, randint
)
from mediawiki import (
    MediaWiki, exceptions
)
from discord import (
    Member, Embed, app_commands, Interaction, ui
)
from discord.app_commands import Choice
from discord.ext import commands, tasks
from discord.errors import HTTPException
from discord.ext.commands import (
    Cog, command, cooldown, BucketType, BadArgument, guild_only, BadLiteralArgument, is_owner
)
from discord.ext.commands.errors import MemberNotFound
from datetime import date, datetime, timedelta
from ..db import db
from ..dizzidb import Dizzidb

sys.path.insert(0, 'C:/Users/HWool/Documents/My Programs/_PyLibraries/dizzimg')
from dizzimg import smash, tiles

DIZZICOLOR = 0x9f4863

def sync_charai(desc="AI image for Kai's character generator"):
    print("Hit 2")
    model = replicate.models.get("stability-ai/sdxl")
    print("Hit 3")
    for ai_output in model.predict(prompt=desc):
        #
        print("Hit 4")
        return ai_output

async def async_charai(desc, bot):
    thing = functools.partial(sync_charai, desc=desc)
    print("hit 1")
    image = await bot.loop.run_in_executor(None, thing)
    #these variable names are aids but I'm in no condition to change them right now
    print("hit 5")
    return image


class Fun(Cog):
    """Test description for fun cog"""
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        # tree = bot.tree


    class TestButton(ui.View):

        class TestModal(ui.Modal, title="Do you know the character?"):
            answer = ui.TextInput(label="Your Answer:")
            #todo: establish the user
            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message(f'You responded with: {self.answer.value}\nNote: If you kept the guessing window open between rounds, your guess may not have counted!', ephemeral=True)
                self.user = interaction.user
                self.interaction = interaction
                return self.user, self.answer.value


        def __init__(self, loops, answer, expire=None):
            super().__init__(timeout=15)
            self.value = None
            self.loops = loops
            self.winner = None
            self.guess = None
            self.answer = answer
            self.curtime = datetime.now()
            self.expire = expire

        # When the confirm button is pressed, set the inner value to `True` and
        # stop the View from listening to more input.
        # We also send the user an ephemeral message that we're confirming their choice.
        @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            #await interaction.response.send_message('Confirming', ephemeral=True)

            if self.expire is not None:
                if self.curtime < self.expire:
                    modal = self.TestModal(timeout=7)
                    await interaction.response.send_modal(modal)
                    await modal.wait()
                    try:
                        if modal.answer.value.lower() == self.answer.lower():
                            self.winner = modal.user
                            self.stop()
                    except AttributeError:
                        pass
                else:
                    self.stop()
            else:
                await interaction.response.send_message("Please wait a moment for the quiz to start!", ephemeral=True)

        
    @commands.hybrid_command(name="roll",
        aliases=["r"],
        brief="Roll some dice",
        usage="`*PREF*roll <die_string>` - Rolls dice. A valid `<die string>` is in the format XdY+Z or XdY-Z,"
        " where X is the number of dies to roll, Y is the value of the die, and Z is a bonus to apply at the end.\n"
        "Example: `*PREF*roll 2d20+5`")
    @app_commands.rename(die_string="dice")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def roll_dice(self, ctx: commands.Context, *, die_string: str) -> None:
        """Rolls a dice with optional bonus (+ or -)"""
        try:
            dnum, dval = (dice for dice in die_string.lower().split("d"))

            dnum = int(dnum)
        
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
        except ValueError:
            await ctx.send("Error: Dice must be in the form XdY+Z or XdY-Z, where X, Y, and Z are numbers between 1 and 100. See ``/help roll`` for more info.", ephemeral=True)
            return

    @commands.hybrid_command(name="slap",
            aliases=["hit"],
            brief="Slap someone for a reason",
            usage="`*PREF*slap <member> <reason>` - Slaps a `<member>` for a `<reason>`. The `<member>` should be properly"
            " pinged with @, the `<reason>` can be any text string to display after the slap. \nExample: `*PREF*slap @dizzi for no reason`")
    @app_commands.rename(member="user")
    @app_commands.checks.cooldown(2, 5, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def slap_member(self, ctx: commands.Context, member: Member, *, reason: str = "") -> None:
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
        

    @commands.hybrid_command(name="art",
            aliases=["avatar"],
            brief="Credits for my wonderful avatar",
            usage="`*PREF*art` - Credit where credit is due\nExample: `*PREF*art`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def art_source(self, ctx: commands.Context) -> None:
        """Art credits for Dizzi's amazing avatar"""
        embed = Embed(title=f"Dizzi Art Source", description="Avatar is by @holdenkip.art on Instagram", color=DIZZICOLOR)
        embed.set_image(url=ctx.guild.me.avatar)
        await ctx.send(embed=embed)

    @slap_member.error
    async def slap_member_error(self, ctx, exc):
        if isinstance(exc, MemberNotFound):
            await ctx.send("I can't find that user. Make sure you ping them!", ephemeral=True)
            return
        
    @command(name="echo",
            aliases=["say"],
            brief="Repeat stuff, repeat stuff",
            usage="`*PREF*echo <message>` - Dizzi will repeat `<message>`\nExample: `*PREF*echo Hello World!`")
    @guild_only()
    async def echo_member(self, ctx, *, message) -> None:
        """Turn your own measly words into the words of the powerful Dizzi."""
        await ctx.message.delete()
        await ctx.send(message)


    @commands.hybrid_command(name="animalfact",
            aliases=["af"],
            brief="Get a fact about an animal",
            usage="`*PREF*animalfact <animal>` - gives a random animal fact and picture for a supported `<animal>`.\n"
            "Example: `*PREF*animalfact koala`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def animal_fact(self, ctx: commands.Context, animal: Literal['dog', 'cat', 'panda', 'fox', 'koala', 'bird', 'raccoon', 'kangaroo']) -> None:
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
            
            async with aiohttp.request("GET", URL, headers={}) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = Embed(title=f"{animal.title()} fact", description=data["fact"], color=DIZZICOLOR)
                    embed.set_thumbnail(url=data["image"])
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"API returned a {response.status} status.")
        else:
            await ctx.send("No facts are available for that animal. Use help animalfact to get a list of supported animals.")
            
    @commands.hybrid_command(name="morelike",
            aliases=["ml"],
            brief="Get a scathing rhyme",
            usage="`*PREF*morelike <rhyme>` - gives you a word that rhymes with `<rhyme>`.\nExample: `*PREF*morelike Dog`")
    @app_commands.checks.cooldown(2, 10)
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def more_like(self, ctx: commands.Context, rhyme: str) -> None:
        """Get a scathing rhyme about a word of your choice. Useless? More like lupus.
        Powered by https://rhymebrain.com/"""

        #remove whitespace
        rhyme.replace(" ", "")
        URL = f"https://rhymebrain.com/talk?function=getRhymes&word={rhyme.lower()}"
        async with aiohttp.request("GET", URL, headers={}) as response:
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
                await ctx.send(f"Error: API returned a {response.status} status. This is probably not Dizzi's fault. Try again later.")
    
    @commands.hybrid_command(name="wikipedia",
            aliases=["wp"],
            brief="Search up an article on wikipedia",
            usage="`*PREF*wikipedia <page>` - gives a brief summary for the given wikipedia `<page>`. "
            "If an exact match is not found, the closest relevant one will be given.\nExample: `*PREF*wikipedia discord`")
    @app_commands.checks.cooldown(2, 10)
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def wikipedia_member(self, ctx: commands.Context, *, page: str) -> None:
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
            aliases=["tabs", "alarm"],
            brief="Keep tabs on someone and be alerted the next time they post something",
            usage="`*PREF*alert <user>` - Will alert you the next time a user posts something.\nExample: `*PREF*alert @hapaboba`")
    @guild_only()
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

    @commands.hybrid_command(name="deflect",
            brief="Deflect a beam",
            usage="`*PREF*deflect` - It'll take more than that!\nExample: `*PREF*deflect`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def deflect(self, ctx):
        """Deflect a beam of energy so that it'll harmlessly hit a mountain in the background instead."""
        await ctx.send("https://i.imgur.com/MYI8EJh.gif")

    @commands.hybrid_command(name="imposter",
            aliases=["impostor", "sus"],
            brief="Dizzi will become the imposter and impersonate someone",
            usage="`*PREF*imposter <user> <message>` - Dizzi will say `<message>` while pretending to be `<user>`.\nExample: `*PREF*imposter @moe I'm a stupid moron with an ugly face and a big butt`")
    @app_commands.guild_only()
    @app_commands.rename(member="user")
    #/@app_commands.guilds(discord.Object(762125363937411132))
    async def imposter(self, ctx: commands.Context, member: Member, *, message: str) -> None:
        """Dizzi will become the imposter and impersonate a user of your choice. Remember, with great power comes great responsibility!"""
        if ctx.interaction == None:
            await ctx.message.delete()
        avatarbytes = await member.avatar.read()
        imposterhook = await ctx.channel.create_webhook(name="imposterhook", avatar=avatarbytes, reason="Dizzi imposter command")
        await imposterhook.send(content=message, username=member.display_name)
        await imposterhook.delete()

    # @commands.hybrid_command(name="aniquote",
    #         aliases=["aq"],
    #         brief="Get a quote from an anime character. You can either specify a character to get one from, or get a completely random one.",
    #         usage="`*PREF*aniquote <character>` - Get a random quote from the specified anime character. If a character isn't specified, you'll get a random anime character.")
    # async def aniquote(self, ctx: commands.Context, character: Optional[str]) -> None:
    #     if character == None:
            
    @commands.hybrid_group(name="smashbros",
            aliases=["newcomer"],
            fallback="user",
            brief="Dizzi will generate an image for you in the style of a smash newcomer",
            usage="`*PREF*`newcomer <user> <toptext> <bottomtext> - Dizzi will generate the image of the user with the given top and bottom texts.\nExample: `*PREF*`newcomer @john \"John Smith\" \"Joins the Fight!\" ")
    @app_commands.guild_only()
    async def smashbros(self, ctx: commands.Context, member: Member, *, introtext: str):
        memberavatar = await member.avatar.to_file()
        image = smash.Newcomer(toptext=member.display_name, bottext=introtext, topimg=memberavatar.fp)
        output = image.generate(returnbytes=True)
        await ctx.send(file=discord.File(fp=output, filename='newcomer.png'))

    # @smashbros.command(name="custom")
    # async def custsmash(self, ctx: commands.Context, img: discord.Asset)

    @commands.hybrid_command(name="aniquiz")
    @app_commands.guild_only()
    @app_commands.guilds(discord.Object(762125363937411132))
    async def aniquiz(self, ctx: commands.Context):
        curtime = datetime.now()

        endtime = datetime.now() + timedelta(minutes=1)

        expires = []

        for i in range(6):
            if i == 0:
                expires.append(curtime + timedelta(seconds=15))
            else:
                expires.append(expires[i-1] + timedelta(seconds=15))


        answer = "Vegeta"
        loops = 0
        winner = None

        view = self.TestButton(loops=loops, answer=answer)

        embed = Embed(title=f"Aniquiz is starting!",color=DIZZICOLOR)

        await ctx.interaction.response.send_message(embed=embed, view=view)

        await asyncio.sleep(5)

        while curtime < endtime and loops < 5 and winner == None:
            loops += 1
            image = tiles.TileFilter(style="square", size=2**(loops+1), bgcolor="black", space=1, rotation=0).generate(returnbytes=True)
            file = discord.File(fp=image, filename="guess.png")
            #generate the embed
            view.stop()
            if loops % 2 != 0:
                embed = Embed(title=f"Aniquiz! Loop {loops}, execute!",color=DIZZICOLOR)
                embed.set_image(url="attachment://guess.png")
                curtime = datetime.now()
                view = self.TestButton(loops=loops, answer=answer, expire=expires[loops])
                #edit the interaction
                await ctx.interaction.edit_original_response(attachments=[file], embed=embed, view=view)
                await view.wait()
                winner = view.winner
            else:
                embed= Embed(title=f"No right answers!", description="Too hard? Let's make it easier!")
                view = self.TestButton(loops=loops, answer=answer)
                await ctx.interaction.edit_original_response(attachments=[], embed=embed, view=None)
                await asyncio.sleep(5)


        if not winner:
            embed = Embed(title=f"Nobody won! The answer was: {answer}",color=DIZZICOLOR)
            await ctx.interaction.edit_original_response(embed=embed, view=None)
        else:
            embed = Embed(title=f"Winner! {winner.name} guessed: {answer}",color=DIZZICOLOR)
            await ctx.interaction.edit_original_response(embed=embed, view=None)

    @commands.hybrid_command(name="character",
            aliases=["char"],
            brief="Create a randomly generated DnD character (code courtesy of Kai Nakamura)",
            usage="`*PREF*character <name> <skills>` - Try out a random character, with the name `<name>` and the skills `<skills>`\nExample: `*PREF*character Scrimblo Pyromancy`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def chargen(self, ctx: commands.Context, name:str, *, skills:str) -> None:
        """Kai Nakamura's fantastic character generator!"""
        #legacy from the OG program from Kai
        #name = input("Character Name: ")
        #skills = input("What is one thing this character good at?: ")

        diceroll = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        diceroll2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        x = choice(diceroll)
        y = choice(diceroll2)

        #make a list for races
        races = ["Roll again", "Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf", "Human", "Halfling", "Half-Orc", "Tiefling", "Genasi", "Aarakocra", "Tabaxi", "Tortle"]

        #make list for class
        classes = ["Roll again", "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]


        await ctx.send(f"{name}, sounds like an adventurer who is a {races[x]}, {classes[y]} who's good at {skills}")
        generatemsg = await ctx.send("Generating an image")

        #my own ai generation stuff
        ai_output = await async_charai(f"A {races[x]} {classes[y]} adventurer who's good at {skills}", self.bot)
        await generatemsg.edit(content=f"{ctx.author.mention}\'s character, {name}: \n{ai_output}")

    @Cog.listener()
    async def on_message(self, message):
        #used to check if a user is needed in the alert system
        #ignore bots
        if (not message.author.bot) and (message.guild is not None):
            #create a userdb
            userdb = Dizzidb(message.author, message.guild)

            if db.dbexist("alert", "dbid", userdb.dbid):
                ctx = await self.bot.get_context(message)
                alertset = userdb.dbluset("alert", "alertset", userdb.dbid)
                #now have the alertset, which should be set in the ;tabs command
                for u in alertset:
                    ping = await self.bot.fetch_user(u)
                    await ctx.send(f"{message.author.name} is online, {ping.mention}!")
                alertset = []
                db.execute("DELETE FROM alert WHERE dbid = ?", userdb.dbid)
            else:
                return


    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
            
async def setup(bot):
    await bot.add_cog(Fun(bot))