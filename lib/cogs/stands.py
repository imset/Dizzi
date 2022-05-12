import aiohttp
import asyncio
import csv
import re
import string
import discord
from typing import Literal
from discord.ext import commands
from random import (
    choice, randint, randrange
)

from datetime import date, datetime
from discord import (
    Member, Embed, app_commands, Interaction
)
from discord.ext.commands import (
    Cog, command, cooldown, BucketType, BadArgument, guild_only
)
from typing import Optional
from discord.ext import tasks
from discord.errors import HTTPException
from ..db import db
from ..dizzidb import Dizzidb, dbprefix

DIZZICOLOR = 0x9f4863

#lastfm api token
#todo before dizzi is released publicly: include specific error checking for if dizzi is setup without this file.
with open("./lib/bot/lastfm.0", "r", encoding="utf=8") as tf:
    LASTTOKEN = tf.read()

#eventually this should be a function to generate stands
def standgenerator(userdb):
    return

#used to convert stand stats from numbers to letters. stats are numbers in the backend for convenience in changing them.
#todo: change this system to be more robust, maybe with +'s and -'s
def standstathandler(stat_value):
    letterstats = []
    for i in stat_value:
        if int(i) == 0:
            letterstats.append("F")
        elif int(i) == 1:
            letterstats.append("D")
        elif int(i) == 2:
            letterstats.append("C")
        elif int(i) == 3:
            letterstats.append("B")
        elif int(i) == 4:
            letterstats.append("A")
    return letterstats

#act changing system. Must be passed in the raw tags data.
#todo: proper commenting
def actchange(name, tags):
    with open('./data/db/superpowers.csv') as s:
        reader = csv.DictReader(s)
        candidates = []
        tags_list = tags.lower().replace(" ", "").split(",")
        i = 0
        while i < 5:
            chosen_tag = choice(tags_list)
            for row_number, row in enumerate(reader):
                # print(row_number)
                if chosen_tag in row["tags"].lower().replace(" ", "").split(",") and name != row["name"]:
                    candidates.append(row)
            i += 1

        print(tags_list)
        print(chosen_tag)

        if candidates != []:
            newstand = choice(candidates)
        else:
            newstand = False

        return [newstand, chosen_tag]

class Stands(Cog):
    def __init__(self, bot):
            self.bot = bot
            #starts daily reset function
            self.dailyreset.start()

    @commands.hybrid_command(name="standroll",
        aliases=["sr"],
        brief="Take hold of your destiny and acquire a stand of your own",
        usage="`*PREF*standroll` - Grab hold of your destiny.\nExample: `*PREF*standroll`")
    @app_commands.guild_only()
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def roll_stand(self, ctx):
        """Indeed Jotaro, what you have called an "evil spirit" is but a powerful vision created by your own life energy! And since it stands next to you, it is called... a **Stand!** """
        userdb = Dizzidb(ctx.author, ctx.guild)
        hadstand = False

        #check if the user is in the db yet
        if db.dbexist("stand", "UserID", userdb.uid):            #pull up their arrowhead amount
            arrows = db.field(f"SELECT arrowheads FROM arrows WHERE UserID = ?", userdb.uid)
            #need 3 to reroll. Upgrade this to 5 once the combat system is in place to let people steal arrows from others.
            if int(arrows) > 2:
                arrowmsg = await ctx.send(f"You currently have **{arrows}** arrowheads. Use 3 to roll a new stand?")
                await arrowmsg.add_reaction('🏹')
                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) == '🏹'

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("Cancelled")
                    return
                else:
                    await ctx.send("You brace yourself and pierce your skin with the arrow.\nA new power begins to stir within you!")
                    arrows = int(arrows) - 2
                    db.execute("UPDATE arrows SET arrowheads = ? WHERE UserID = ?", str(arrows), userdb.uid)
                    db.execute("DELETE FROM stand WHERE UserID = (?)", userdb.uid)
                    hadstand = True
            else:
                await ctx.send(f"You don't have enough arrowheads to roll a new stand! \n(Current Arrows: {arrows} | Needed: 3)")

            #await ctx.send(f"Error: You already have a stand! Check it out with {dbprefix(ctx.guild)}standinfo\nWant a new stand? Sorry, but that feature isn't done yet! Accept your fate!")
        if not db.dbexist("stand", "UserID", userdb.uid):
            db.execute("INSERT or IGNORE INTO stand (UserID) VALUES (?)", userdb.uid)
            db.execute("INSERT or IGNORE INTO arrows (UserID) VALUES (?)", userdb.uid)
            arrows = db.field(f"SELECT arrowheads FROM arrows WHERE UserID = ?", userdb.uid)
            arrows = int(arrows) - 1
            db.execute("UPDATE arrows SET arrowheads = ? WHERE UserID = ?", str(arrows), userdb.uid)
            if not hadstand:
                await ctx.send("You find some strange arrowheads. You feel them calling out to you!")

            with open('./data/db/superpowers.csv') as s:
                lines = sum(1 for line in s)
                line_number = randrange(lines)

            with open('./data/db/superpowers.csv') as s:
                reader = csv.DictReader(s)
                try:
                    chosen_row = next(row for row_number, row in enumerate(reader) if row_number == line_number)
                    db.execute("UPDATE stand SET ability = ? WHERE UserID = ?", chosen_row['name'], userdb.uid)
                    db.execute("UPDATE stand SET overview = ? WHERE UserID = ?", chosen_row['overview'], userdb.uid)
                    db.execute("UPDATE stand SET description = ? WHERE UserID = ?", chosen_row['description'], userdb.uid)
                    db.execute("UPDATE stand SET pro1 = ? WHERE UserID = ?", chosen_row['pro1'], userdb.uid)
                    db.execute("UPDATE stand SET pro2 = ? WHERE UserID = ?", chosen_row['pro2'], userdb.uid)
                    db.execute("UPDATE stand SET pro3 = ? WHERE UserID = ?", chosen_row['pro3'], userdb.uid)
                    db.execute("UPDATE stand SET con1 = ? WHERE UserID = ?", chosen_row['con1'], userdb.uid)
                    db.execute("UPDATE stand SET con2 = ? WHERE UserID = ?", chosen_row['con2'], userdb.uid)
                    db.execute("UPDATE stand SET con3 = ? WHERE UserID = ?", chosen_row['con3'], userdb.uid)
                    db.execute("UPDATE stand SET tags = ? WHERE UserID = ?", chosen_row['tags'], userdb.uid)
                    db.execute("UPDATE stand SET total_comparisons = ? WHERE UserID = ?", chosen_row['total_comparisons'], userdb.uid)
                    db.execute("UPDATE stand SET preference_ratio = ? WHERE UserID = ?", chosen_row['preference_ratio'], userdb.uid)
                    db.execute("UPDATE stand SET origin = ? WHERE UserID = ?", chosen_row['origin'], userdb.uid)


                    r = chosen_row['description'].split(" ")
                    wordlist = []
                    #seed = "none"
                    for i in r:
                        if len(i) > 4 and len(i) < 8 and i.lower() != "power":
                            wordlist.append(i)

                    if wordlist == []:
                        wordlist = ["horse", "staple", "queen", "fail", "home", "type", "errand", "clean", "love"]

                    seed = choice(wordlist)
                    print(seed)

                    songtitle = f"https://ws.audioscrobbler.com/2.0/?method=track.search&track={seed}&api_key={LASTTOKEN}&format=json"
                    titleset = set()

                    titlerand = randrange(0, 29)

                    async with aiohttp.request("GET", songtitle, headers={}) as response:
                        if response.status == 200:
                            data = await response.json()
                            #print(data)
                            i = 0
                            for track in data["results"]["trackmatches"]["track"]:
                                if len(track["name"]) < 25 and track["name"] != seed:
                                    titleset.add(track["name"].lower())
                                    titleset.add(track["artist"].lower())
                                    #print(track["track"]["track_name"])
                                i += 1

                    standname = string.capwords(choice(list(titleset)))
                    db.execute("UPDATE stand SET name = ? WHERE UserID = ?", standname, userdb.uid)

                    # standstats = ["4", "3", "2", "1", "0"]
                    # genstats = []
                    # i = 0
                    # while len(genstats) < 6:
                    #     genstats.append(choice(standstats))

                    genstats = []
                    while len(genstats) < 5:
                        genstats.append(str(randint(0,3)))

                    #guarantee potential of D or higher
                    genstats.append(str(randint(1,4)))

                    statstring = ', '.join(genstats)
                    db.execute("UPDATE stand SET stats = ? WHERE UserID = ?", statstring, userdb.uid)

                    #stand type, appearance, traits

                    type_options = ["Close-Range", "Long-Range"]
                    size_options = ["Tiny", "Small", "Medium", "Large", "Huge"]
                    na_options = ["Natural", "Artificial"]
                    natural_options = ["Humanoid", "Animal-Like"]
                    animal_options = ["Lion", "Gorilla", "Dog", "Cat", "Bird", "Shark", "Insect", "Monkey", "Snake", "Lizard", "Plant"]
                    color_options = ["Red", "Blue", "Pink", "Black", "White", "Yellow", "Green", "Orange", "Purple", "Gray"]
                    misc_options = ["a Haunting Smile", "a Soothing Smile", "a Menacing Smile", "a Very Long Tail", "Hollow Eyes", "One Large Eye", 
                                    "an Expressionless Face", "a Golden Mask", "a Silver Mask", "a Copper Mask", "Long Horns", "Large Wings", "Small Wings",
                                    "a Sad Expression", "an Angry Expression", "a Blindfold On", "Thin Limbs", "a Spiky Collar", "Long Hair", "No Hands",
                                    "a Short Sword", "a Battle Axe", "a Pair of Daggers", "a Rapier", "a Long Nose", "a Deep Voice", "a Funny Voice", "a Big Gun",
                                    "Shiny Skin", "Armor", "a Hole in its Chest", "Bulky Shoulder Pads"]


                    standtraits = [choice(type_options), choice(size_options), choice(na_options)]

# 0 = type, 1 = size, 2 = natural or artificial, 3 = humanoid or animal,  4 = animal type, 5 = color, 6 = legs, 7 = arms, 8 and 9 = misc traits

                    if standtraits[2] == "Natural":
                        standtraits.append(choice(natural_options))
                        if standtraits[3] == "Animal-Like":
                            standtraits.append(choice(animal_options))
                        else:
                            standtraits.append("None")
                    else:
                        standtraits.append("Humanoid")
                        standtraits.append("None")

                    if randint(0,2) != 1:
                        standtraits.append(choice(color_options))
                    else:
                        standtraits.append(f"{choice(color_options)} and {choice(color_options)}")

                    standtraits.append(str(randint(2,6)))
                    standtraits.append(str(randint(1,6)))
                    standtraits.append(choice(misc_options))
                    standtraits.append(choice(misc_options))

                    traitstring = ', '.join(standtraits)
                    db.execute("UPDATE stand SET traits = ? WHERE UserID = ?", traitstring, userdb.uid)



                    await ctx.send(f"Success! You got the stand **「{standname}」** with the ability **{chosen_row['name']}**! Use {dbprefix(ctx.guild)}standinfo to check it out.")
                    #await ctx.send(chosen_row['name'])
                except StopIteration:
                    print("StopIteration Error")
                    await ctx.send("Failure! You feel your connection to your stand disappear!\nPerhaps you are not yet fated to have a power of your own yet... try again?")
                    db.execute("DELETE FROM stand WHERE UserID = (?)", userdb.uid)
                except IndexError:
                    print("IndexError Error")
                    await ctx.send("Failure! You feel your connection to your stand disappear!\nPerhaps you are not yet fated to have a power of your own yet... try again?")
                    db.execute("DELETE FROM stand WHERE UserID = (?)", userdb.uid)

    @commands.hybrid_command(name="standinfo",
        aliases=["si"],
        brief="See info about your stand or someone else's",
        usage="`*PREF*standinfo` - Learn about your true powers.\nExample: `*PREF*standinfo`")
    @app_commands.guild_only()
    @app_commands.rename(member="user")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def stand_info(self, ctx, member: Optional[Member]):
        """Tells you info about your stand, if you have one. If not, try ;standroll"""

        if member == None:
            userdb = Dizzidb(ctx.author, ctx.guild)
            if not db.dbexist("stand", "UserID", userdb.uid):
                await ctx.send(f"Error: You don't have a stand! Get your stand with {dbprefix(ctx.guild)}standroll")
            else:
                act = db.field(f"SELECT act FROM stand WHERE UserID = ?", userdb.uid)
                arrows = db.field(f"SELECT arrowheads FROM arrows WHERE UserID = ?", userdb.uid)
                reroll = db.field(f"SELECT rerolls FROM arrows WHERE UserID = ?", userdb.uid)
                charms = db.field(f"SELECT charms FROM arrows WHERE UserID = ?", userdb.uid)
                energy = db.field(f"SELECT energy FROM stand WHERE UserID = ?", userdb.uid)
                standname = db.field(f"SELECT name FROM stand WHERE UserID = ?", userdb.uid)
                standability = db.field(f"SELECT ability FROM stand WHERE UserID = ?", userdb.uid)
                standoverview = db.field(f"SELECT overview FROM stand WHERE UserID = ?", userdb.uid)
                standdesc = db.field(f"SELECT description FROM stand WHERE UserID = ?", userdb.uid)
                pros = [db.field(f"SELECT pro1 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT pro2 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT pro3 FROM stand WHERE UserID = ?", userdb.uid)]
                cons = [db.field(f"SELECT con1 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT con2 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT con3 FROM stand WHERE UserID = ?", userdb.uid)]
                stats = standstathandler(db.field(f"SELECT stats FROM stand WHERE UserID = ?", userdb.uid).split(", "))
                br = db.field(f"SELECT battlerecord FROM stand WHERE UserID = ?", userdb.uid).split(", ")
                traits = db.field(f"SELECT traits FROM stand WHERE UserID = ?", userdb.uid).split(", ")
                origin = int(db.field(f"SELECT origin FROM stand WHERE UserID = ?", userdb.uid))

                if act == 1:
                    embed = Embed(title=f"**Stand Name**: 「{standname}」",color=DIZZICOLOR)
                else:
                    embed = Embed(title=f"**Stand Name**: 「{standname} - Act {act}」",color=DIZZICOLOR)
                #embed.add_field(name="Stand Name:", value=f"「{standname}」\n**Wins:** {br[0]} | **Losses:** {br[1]}")
                embed.add_field(name="Stats:", value=f"Power = {stats[0]}\nSpeed = {stats[1]}\nAbility Range = {stats[2]}\nStamina = {stats[3]}\nPrecision = {stats[4]}\nPotential = {stats[5]}")
                if traits[3] == "Humanoid" and traits[2] == "Natural":
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has a {traits[2]} {traits[3]} appearance with {traits[8]} and {traits[9]}.")
                elif traits[2] == "Artificial":
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has an {traits[2]} {traits[3]} appearance. It has {traits[8]}, {traits[9]}, {traits[6]} Arms, and {traits[7]} Legs.")
                else:
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has a {traits[2]} {traits[3]} appearance. It looks like a {traits[4]} with {traits[8]} and {traits[9]}")

                embed.add_field(name="Ability Overview:", value=f"*{standability}*:\n{standoverview}")
                #embed.add_field(name="Overview:", value=f"{standoverview}")
                embed.add_field(name="Ability Details:", value=f"{standdesc}")
                embed.add_field(name="Effects:", value=f"{pros[0]}\n{pros[1]}\n{pros[2]}")
                embed.add_field(name="Drawbacks:", value=f"{cons[0]}\n{cons[1]}\n{cons[2]}")
                embed.add_field(name="Items:", value=f"Arrowheads: {arrows}\nCharms: {charms}")
                embed.add_field(name="Energy:", value=f"{energy}")
                embed.add_field(name="Battle Record:", value=f"Wins: {br[0]} | Losses: {br[1]}")
                if origin == 0:
                    embed.set_footer(text="\nCopyright © Justin Mahar | The Superpower List")
                embed.set_author(name=f"{ctx.author.display_name}", icon_url=f"{ctx.author.avatar}")

                await ctx.send(embed=embed)
        else:
            userdb = Dizzidb(member, ctx.guild)
            if not db.dbexist("stand", "UserID", userdb.uid):
                await ctx.send(f"Error: That user doesn't have a stand!")
            else:
                act = db.field(f"SELECT act FROM stand WHERE UserID = ?", userdb.uid)
                arrows = db.field(f"SELECT arrowheads FROM arrows WHERE UserID = ?", userdb.uid)
                reroll = db.field(f"SELECT rerolls FROM arrows WHERE UserID = ?", userdb.uid)
                charms = db.field(f"SELECT charms FROM arrows WHERE UserID = ?", userdb.uid)
                energy = db.field(f"SELECT energy FROM stand WHERE UserID = ?", userdb.uid)
                standname = db.field(f"SELECT name FROM stand WHERE UserID = ?", userdb.uid)
                standability = db.field(f"SELECT ability FROM stand WHERE UserID = ?", userdb.uid)
                standoverview = db.field(f"SELECT overview FROM stand WHERE UserID = ?", userdb.uid)
                standdesc = db.field(f"SELECT description FROM stand WHERE UserID = ?", userdb.uid)
                pros = [db.field(f"SELECT pro1 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT pro2 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT pro3 FROM stand WHERE UserID = ?", userdb.uid)]
                cons = [db.field(f"SELECT con1 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT con2 FROM stand WHERE UserID = ?", userdb.uid), db.field(f"SELECT con3 FROM stand WHERE UserID = ?", userdb.uid)]
                stats = standstathandler(db.field(f"SELECT stats FROM stand WHERE UserID = ?", userdb.uid).split(", "))
                br = db.field(f"SELECT battlerecord FROM stand WHERE UserID = ?", userdb.uid).split(", ")
                traits = db.field(f"SELECT traits FROM stand WHERE UserID = ?", userdb.uid).split(", ")

                if act == 1:
                    embed = Embed(title=f"**Stand Name**: 「{standname}」",color=DIZZICOLOR)
                else:
                    embed = Embed(title=f"**Stand Name**: 「{standname} - Act {act}」",color=DIZZICOLOR)
                #embed.add_field(name="Stand Name:", value=f"「{standname}」\n**Wins:** {br[0]} | **Losses:** {br[1]}")
                embed.add_field(name="Stats:", value=f"Power = {stats[0]}\nSpeed = {stats[1]}\nAbility Range = {stats[2]}\nStamina = {stats[3]}\nPrecision = {stats[4]}\nPotential = {stats[5]}")
                if traits[3] == "Humanoid" and traits[2] == "Natural":
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has a {traits[2]} {traits[3]} appearance with {traits[8]} and {traits[9]}.")
                elif traits[2] == "Artificial":
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has an {traits[2]} {traits[3]} appearance. It has {traits[8]}, {traits[9]}, {traits[6]} Arms, and {traits[7]} Legs.")
                else:
                    embed.add_field(name="Appearance:",
                                    value=f"「{standname}」 is a {traits[1]} {traits[5]} {traits[0]} Stand. It has a {traits[2]} {traits[3]} appearance. It looks like a {traits[4]} with {traits[8]} and {traits[9]}")

                embed.add_field(name="Ability Overview:", value=f"*{standability}*:\n{standoverview}")
                #embed.add_field(name="Overview:", value=f"{standoverview}")
                embed.add_field(name="Ability Details:", value=f"{standdesc}")
                embed.add_field(name="Effects:", value=f"{pros[0]}\n{pros[1]}\n{pros[2]}")
                embed.add_field(name="Drawbacks:", value=f"{cons[0]}\n{cons[1]}\n{cons[2]}")
                embed.add_field(name="Items:", value=f"Arrowheads: {arrows}\nCharms: {charms}")
                embed.add_field(name="Energy:", value=f"{energy}")
                embed.add_field(name="Battle Record:", value=f"Wins: {br[0]} | Losses: {br[1]}")
                embed.set_footer(text="\nCopyright © Justin Mahar | The Superpower List")
                embed.set_author(name=f"{ctx.author.display_name}", icon_url=f"{ctx.author.avatar}")


                await ctx.send(embed=embed)

    # @command(name="approach",
    # aliases=["a"],
    # brief="Approach someone for combat (not yet implemented)",
    # usage="`*PREF*approach` - Stand Users Attract Other Stand Users.\nExample: `*PREF*approach @dizzi`")
    # @guild_only()
    # async def approach(self, ctx, member: Optional[Member]):
    #     """Approach someone for combat (not yet implemented)"""
    #     if member != None:
    #         await ctx.send(f"Oh? You're approaching {member.display_name}? Instead of waiting for this command to actually be implemented, you're coming right at them?")
    #     else:
    #         await ctx.send(f"Oh? You're approaching someone? Instead of waiting for this command to actually be implemented, you're coming right at them?")


    @commands.hybrid_command(name="standshop",
                            aliases=["shop"],
                            brief="Buy items to improve and protect your stand",
                            usage="`*PREF*shop` - Check out the fortune teller's shop.\n`*PREF*shop <item>` - Buy an item.\nExample: `*PREF*shop Daily`")
    @app_commands.guild_only()
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def shop(self, ctx, *, item: Literal['daily', 'enhancer', 'changer', 'browse']):
        """Check out the mysterious fortune teller's shop.
        Item descriptions:
        `daily` - A Daily bonus of free arrowheads. Can give between 1 and 3.
        `enhancer` - Enhances your stand. Randomly increases stats, but always lowers potential by 1 stage.
        `changer` - Randomly increases stats, guaranteed to increase potential by 1 stage, and gives the stand a new ability that is somehow related to their old one.
        `charm` - Stops an enemy from messing with your stand if they beat you in combat.
        `snack` - Gives +20% energy for your weary stand
        `seance` - Remove a curse from your stand
        """
        userdb = Dizzidb(ctx.author, ctx.guild)
        arrows = db.field(f"SELECT arrowheads FROM arrows WHERE UserID = ?", userdb.uid)
        dailystatus = db.field(f"SELECT shopclaim FROM arrows WHERE UserID = ?", userdb.uid)

        if item == None or item.lower() == 'browse':
            embed = Embed(title=f"Fortune Teller's Shop", description="Welcome! \nCare to take a look at my wares?", color=DIZZICOLOR)
            embed.set_thumbnail(url="https://static.jojowiki.com/images/thumb/5/5c/latest/20200809171105/Avdol_Infobox_OVA.png/400px-Avdol_Infobox_OVA.png")
            embed.set_footer(text=f"You have {arrows} arrowheads. \nBuy items with {dbprefix(ctx.guild)}shop <item>\nWant to know what an item does? Try {dbprefix(ctx.guild)}help shop")
            #embed.add_field(name="Welcome!", value="")
            if dailystatus == 0:
                embed.add_field(name=f"————————————————\n", value="**Daily** - [FREE]", inline=False)
            embed.add_field(name=f"————————————————\n", value="**Enhancer** - [1 Arrowhead]", inline=False)
            embed.add_field(name=f"————————————————\n", value="**Changer** - [3 Arrowheads]", inline=False)
            #embed.add_field(name=f"————————————————\n", value="**Reroller** - [5 Arrowheads]", inline=False)
            #embed.add_field(name=f"————————————————\n", value="**Ward Charm** - [5 Arrowheads]", inline=False)
            #embed.add_field(name=f"————————————————\n", value="**Soul Snack** - [10 Arrowheads]", inline=False)

            await ctx.send(embed=embed)

        elif item.lower().replace(" ", "") == "daily":
            if dailystatus == 1:
                await ctx.send("Sorry, I've already given you your daily arrows. Try again later!")
            else:
                #dailyarrows = randint(1, 3)
                #guarantee 3 daily arrows during rewrite period
                dailyarrows = 3
                await ctx.send(f"You open your daily box. Inside are {dailyarrows} arrowheads!")
                arrows = arrows + dailyarrows
                db.execute("UPDATE arrows SET arrowheads = ? WHERE UserID = ?", arrows, userdb.uid)
                db.execute("UPDATE arrows SET shopclaim = ? WHERE UserID = ?", 1, userdb.uid)

        elif item.lower().replace(" ", "") == "enhancer" or item.lower().replace(" ", "") == "enhance" or item.lower().replace(" ", "") == "e":
            stats = db.field(f"SELECT stats FROM stand WHERE UserID = ?", userdb.uid).split(", ")
            if arrows < 1:
                await ctx.send(f"Whoops! You need {1 - arrows} more arrowheads to buy that!")
            elif int(stats[5]) == 0 or (int(stats[0]) == 4 and int(stats[1]) == 4 and int(stats[2]) == 4 and int(stats[3]) == 4 and int(stats[4]) == 4):
                await ctx.send(f"Your stand cannot be enhanced as it has already reached its maximum potential.")
            else:
                await ctx.send(f"You buy the Enhancer. You feel as though your stand has become stronger!")
                embed = Embed(title=f"Stand Stat Enhancement", color=DIZZICOLOR)
                statfrmt = standstathandler(stats)

                embed.add_field(name="Old Stats:", value=f"Power = {statfrmt[0]}\nSpeed = {statfrmt[1]}\nAbility Range = {statfrmt[2]}\nStamina = {statfrmt[3]}\nPrecision = {statfrmt[4]}\nPotential = {statfrmt[5]}")
                #how many stat increases the user gets
                stat_increases = randint(1,3)
                newstats = stats.copy()

                while stat_increases > 0:
                    bucket = randint(0,4)
                    if int(newstats[0]) == 4 and int(newstats[1]) == 4 and int(newstats[2]) == 4 and int(newstats[3]) == 4 and int(newstats[4]) == 4:                        
                        break
                    elif int(newstats[bucket]) == 4:
                        continue
                    else:
                        ns_fix = int(newstats[bucket])
                        newstats[bucket] = str(ns_fix + 1)
                        stat_increases -= 1

                newstats[5] = str(int(newstats[5]) - 1)
                newstatfrmt = standstathandler(newstats)
                i = 0
                while i < 6:
                    if int(newstats[i]) != int(stats[i]):
                        newstatfrmt[i] = f"**{newstatfrmt[i]}**"
                    i += 1

                arrows -= 1
                db.execute("UPDATE arrows SET arrowheads = ? WHERE UserID = ?", arrows, userdb.uid)
                embed.add_field(name="New Stats:", value=f"Power = {newstatfrmt[0]}\nSpeed = {newstatfrmt[1]}\nAbility Range = {newstatfrmt[2]}\nStamina = {newstatfrmt[3]}\nPrecision = {newstatfrmt[4]}\nPotential = {newstatfrmt[5]}")
                
                statstring = ', '.join(newstats)
                db.execute("UPDATE stand SET stats = ? WHERE UserID = ?", statstring, userdb.uid)
                await ctx.send(embed=embed)
        elif item.lower().replace(" ", "") == "actchanger" or item.lower().replace(" ", "") == "actchange" or item.lower().replace(" ", "") == "ac":
            
            if arrows < 1:
                await ctx.send(f"Whoops! You need {1 - arrows} more arrowheads to buy that!")
            else:
                arrows -= 3
                act = db.field(f"SELECT act FROM stand WHERE UserID = ?", userdb.uid)

                ac_data = actchange(db.field(f"SELECT ability FROM stand WHERE UserID = ?", userdb.uid),db.field(f"SELECT tags FROM stand WHERE UserID = ?", userdb.uid))

                if ac_data[0] == False:
                    await ctx.send("Failure! Your stand couldn't handle moving to the next act, and it disappeared completely!")
                    return

                chosen_row = ac_data[0]
                
                db.execute("UPDATE stand SET ability = ? WHERE UserID = ?", chosen_row['name'], userdb.uid)
                db.execute("UPDATE stand SET overview = ? WHERE UserID = ?", chosen_row['overview'], userdb.uid)
                db.execute("UPDATE stand SET description = ? WHERE UserID = ?", chosen_row['description'], userdb.uid)
                db.execute("UPDATE stand SET pro1 = ? WHERE UserID = ?", chosen_row['pro1'], userdb.uid)
                db.execute("UPDATE stand SET pro2 = ? WHERE UserID = ?", chosen_row['pro2'], userdb.uid)
                db.execute("UPDATE stand SET pro3 = ? WHERE UserID = ?", chosen_row['pro3'], userdb.uid)
                db.execute("UPDATE stand SET con1 = ? WHERE UserID = ?", chosen_row['con1'], userdb.uid)
                db.execute("UPDATE stand SET con2 = ? WHERE UserID = ?", chosen_row['con2'], userdb.uid)
                db.execute("UPDATE stand SET con3 = ? WHERE UserID = ?", chosen_row['con3'], userdb.uid)
                db.execute("UPDATE stand SET tags = ? WHERE UserID = ?", chosen_row['tags'], userdb.uid)
                db.execute("UPDATE stand SET total_comparisons = ? WHERE UserID = ?", chosen_row['total_comparisons'], userdb.uid)
                db.execute("UPDATE stand SET preference_ratio = ? WHERE UserID = ?", chosen_row['preference_ratio'], userdb.uid)

                db.execute("UPDATE stand SET act = ? WHERE UserID = ?", int(act) + 1, userdb.uid)

                #stat enhancement
                stats = db.field(f"SELECT stats FROM stand WHERE UserID = ?", userdb.uid).split(", ")

                embed = Embed(title=f"Stand Act Change - Stat Upgrades", color=DIZZICOLOR)
                statfrmt = standstathandler(stats)

                embed.add_field(name="Old Stats:", value=f"Power = {statfrmt[0]}\nSpeed = {statfrmt[1]}\nAbility Range = {statfrmt[2]}\nStamina = {statfrmt[3]}\nPrecision = {statfrmt[4]}\nPotential = {statfrmt[5]}")
                #how many stat increases the user gets
                stat_increases = randint(1,3)
                newstats = stats.copy()

                while stat_increases > 0:
                    bucket = randint(0,4)
                    if int(newstats[0]) == 4 and int(newstats[1]) == 4 and int(newstats[2]) == 4 and int(newstats[3]) == 4 and int(newstats[4]) == 4:                        
                        break
                    elif int(newstats[bucket]) == 4:
                        continue
                    else:
                        ns_fix = int(newstats[bucket])
                        newstats[bucket] = str(ns_fix + 1)
                        stat_increases -= 1

                if int(newstats[5]) != 4:
                    newstats[5] = str(int(newstats[5]) + randint(1, 4 - int(newstats[5])))

                newstatfrmt = standstathandler(newstats)
                i = 0
                while i < 6:
                    if int(newstats[i]) != int(stats[i]):
                        newstatfrmt[i] = f"**{newstatfrmt[i]}**"
                    i += 1

                
                db.execute("UPDATE arrows SET arrowheads = ? WHERE UserID = ?", arrows, userdb.uid)
                embed.add_field(name="New Stats:", value=f"Power = {newstatfrmt[0]}\nSpeed = {newstatfrmt[1]}\nAbility Range = {newstatfrmt[2]}\nStamina = {newstatfrmt[3]}\nPrecision = {newstatfrmt[4]}\nPotential = {newstatfrmt[5]}")

                statstring = ', '.join(newstats)
                db.execute("UPDATE stand SET stats = ? WHERE UserID = ?", statstring, userdb.uid)

                await ctx.send(f"Success. Your stand has upgraded to **Act {act + 1}**\nYour stand's new ability is {chosen_row['name']}\nIt's related to your old ability through the following trait: **{ac_data[1]}**")
                await ctx.send(embed=embed)
        else:
            await ctx.send(f"Sorry, I didn't understand that. Check {dbprefix(ctx.guild)}shop for valid items.")

    @tasks.loop(minutes = 60.0)
    async def dailyreset(self):
        if datetime.now().hour == 1:
            db.execute("UPDATE arrows SET shopclaim = ?", 0)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("stands")

async def setup(bot):
        await bot.add_cog(Stands(bot))