import re
import io
import asyncio
import discord
from aiohttp import request, ClientSession
from discord import (
    Member, Embed
)
from discord.ext.commands import (
    Cog, command, BadArgument, MemberNotFound, guild_only
)
from discord.ext import tasks
from discord.ext.menus import (
    MenuPages, ListPageSource
)
from datetime import date, datetime
from ..db import db
from ..dizzidb import Dizzidb, dbprefix

DIZZICOLOR = 0x2c7c94

class BdMenu(ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        # #immediately sort the all the data in the list by the second index
        data = sorted(data, key=lambda x:(x[1]))
        super().__init__(data, per_page=10)

    async def write_page(self, menu, fields=[]):
        #offset for footers and rankings
        offset = (menu.current_page*self.per_page) + 1
        len_data = len(self.entries)

        # #the member is always given redundantly at index 2 of the list
        # member = fields[0][0]

        #create embed
        embed = Embed(title=f"Server Birthday List", description="You wouldn't forget, would you?", color=DIZZICOLOR)
        embed.set_thumbnail(url="https://i.imgur.com/EpCy2fT.png")    
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} Birthdays.")

        #i is used for the ranking value of emojis
        i = offset
        for member, value in fields:
            #generates the fields with the emoji and its ranking
            embed.add_field(name=f"————————————————\n", value=f"**{member.display_name}: {value}**", inline=False)
            i += 1

        return embed

    async def format_page(self, menu, entries):
        fields = []
        
        for member, value in entries:
            #creates the field list that will be used in write_page to add fields
            fields.append([member, value])

        # #sorts again (seems redundant but stuff breaks without this for some reason)
        # fields = sorted(fields, key=lambda x: (x[1]), reverse=True)

        return await self.write_page(menu, fields)

class Birthday(Cog):
    """Test description for birthday cog"""
    def __init__(self, bot):
        self.bot = bot
        self.bdchk.start()
        self.wishedreset.start()

    @command(name="birthdayadd",
            aliases=["bdadd", "bda"],
            brief="Add a birthday to the birthdatabase",
            usage="`*PREF*birthdayadd <user>` -Adds a user to the birthday database so they'll be wished a happy birthday. Accepts dates formatted as MM/DD/YY, MM/DD/YYYY, or in a format such as February 27th, 1980. Birthyear is optional. Birthday messages will be output to the welcome channel.\nExample: `*PREF*bdadd @dizzi 10/03`\n`*PREF*bdadd @dizzi Oct 03`")
    @guild_only()
    async def bd_add(self, ctx, member: Member, *, day: str):
        """Add a user to Dizzi's birthday database"""

        # if isinstance(exc, MemberNotFound):
        #     await ctx.send("Sorry, I don't understand")

        if member.bot == True and member.name == "Dizzi":
            await ctx.send(f"I'm flattered, but I already know my birthday is October 3rd!")
            return
        elif member.bot == True:
            await ctx.send(f"Sorry, I don't wish birthdays to weird bots like {member.display_name}.")
            return

        #first check if string has '/' for the format xx/xx/xxxx
        if "/" in day:
            day.strip()
            daylist = day.split('/')
            if len(daylist[0]) == 1:
                monthval = f"0{daylist[0]}"
            else:
                monthval = daylist[0]
            if len(daylist[1]) == 1:
                dayval = f"0{daylist[1]}"
            else:
                dayval = daylist[1]

            if len(daylist) >= 3:
                if len(daylist[2]) == 1:
                    yearval = f"0{daylist[2]}"
                else:
                    yearval = daylist[2]
            else:
                yearval = 0
        else:
            #make everything lowercase
            day = day.lower()
            #now we need to search for a month, day, and year. Year should be 4 digits, month will be searched with a month code, day will be what's left
            #by default we assume the date is split by spaces here
            daylist = day.split(' ')
            for i in daylist:
                if "jan" in i:
                    monthval = "01"
                    break
                elif "feb" in i:
                    monthval = "02"
                    break
                elif "mar" in i:
                    monthval = "03"
                    break
                elif "apr" in i:
                    monthval = "04"
                    break
                elif "may" in i:
                    monthval = "05"
                    break
                elif "jun" in i:
                    monthval = "06"
                    break
                elif "jul" in i:
                    monthval = "07"
                    break
                elif "aug" in i:
                    monthval = "08"
                    break
                elif "sep" in i:
                    monthval = "09"
                    break
                elif "oct" in i:
                    monthval = "10"
                    break
                elif "nov" in i:
                    monthval = "11"
                    break
                elif "dec" in i:
                    monthval = "12"
                    break

            #now that we have the month, we need to disambiguate the year and the day. Using code from https://www.sanfoundry.com/python-program-count-number-digits/
            #to count digits - years should be 4 digits, day should be 1 or 2.

            #first remove all non-digits from each entry in daylist.
            # i0 = re.sub('\D', '', daylist[0])
            # i1 = re.sub('\D', '', daylist[1])
            # i2 = re.sub('\D', '', daylist[2])

            i = 0
            daylisttemp = []
            while i < len(daylist):
                daylisttemp.append(re.sub('\D', '', daylist[i]))
                i += 1

            #now we need to iterate over each one and find the 4 digit year
            for i in daylisttemp:
                if i == '':
                    continue
                j = int(i)
                count=0
                while(j>0):
                    count=count+1
                    j=j//10
                if count == 4:
                    yearval = i
                else:
                    if len(i) == 1:
                        dayval = f"0{i}"
                    else:
                        dayval = i

            try:
                #shorten the year to the last two digits
                yearval = str(yearval)[-2:]
            except:
                yearval = 0


        finalmonthday = f"{monthval}/{dayval}"


        #set the Dizzidb object as the mentioned member for lookup, also create normal userdb
        memberdb = Dizzidb(member, member.guild)
        #add them to the database
        db.execute("INSERT or IGNORE INTO birthday (dbid) VALUES (?)", memberdb.dbid)
        #add the user's dbid into the alertdict
        db.execute("UPDATE birthday SET monthday = ? WHERE dbid = ?", finalmonthday, memberdb.dbid)
        db.execute("UPDATE birthday SET year = ? WHERE dbid = ?", yearval, memberdb.dbid)
        if yearval != 0:
            await ctx.send(f"Alright, I've added {finalmonthday}/{yearval} as {member.name}'s birthday. I'll be sure to wish them a happy birthday!")
        else:
            await ctx.send(f"Alright, I've added {finalmonthday} as {member.name}'s birthday. I'll be sure to wish them a happy birthday!")

    @bd_add.error
    async def bd_add_error(self, ctx, exc):
        if isinstance(exc, MemberNotFound):
            await ctx.send("Sorry, something went wrong processing your command. Make sure you @ the user you want to add a birthday for and use a valid date.")

    @command(name="birthdaylist",
            aliases=["bdlist", "bdl"],
            brief="Show the list of birthdays on this server",
            usage="`*PREF*birthdaylist` - Shows the birthday list.\nExample: `*PREF*bdlist`")
    @guild_only()
    async def bd_list(self, ctx):
        """Show a list of user birthdays on your server."""

        bdset = db.records("SELECT dbid, monthday FROM birthday WHERE dbid LIKE ?", f"%.{ctx.guild.id}")

        #note for the future - this is slow

        bdconvset = []
        for i in bdset:
            bdconvset.append(list(i))

        i = 0
        while i < len(bdconvset):
            userid = bdconvset[i][0].split('.')[0]
            guildid = bdconvset[i][0].split('.')[1]
            #get member instead of user
            guild = await self.bot.fetch_guild(guildid)
            #u = await self.bot.fetch_user(userid)
            u = await guild.fetch_member(userid)
            bdconvset[i][0] = u
            i += 1


        #print(bdconvset)
        menu = MenuPages(source=BdMenu(ctx, bdconvset))
        await menu.start(ctx)


    #birthday task loop
    @tasks.loop(minutes = 60.0)
    async def bdchk(self):
        #check if there's any birthdays today
        todaybds = db.column("SELECT dbid FROM birthday WHERE monthday = ?", str(date.today().strftime("%m/%d")))
        if todaybds == [] or todaybds == "":
            return
        else:
            for i in todaybds:
                wished = db.field("SELECT wished FROM birthday WHERE dbid = ?", i)
                if wished == 0 and datetime.now().hour >= 8:
                    splitset = i.split(".")
                    bduser = await self.bot.fetch_user(splitset[0])
                    bdguild = await self.bot.fetch_guild(splitset[1])
                    userdb = Dizzidb(bduser, bdguild)
                    welcomechannel = db.field("SELECT Welcome FROM guildsettings WHERE GuildID = ?", userdb.gid)
                    ping = await self.bot.fetch_user(userdb.uid)
                    #print(f"Happy birthday to {ping.display_name}")
                    channelpush = await self.bot.fetch_channel(int(welcomechannel))

                    await channelpush.send(f"**🎉Today is {ping.mention}'s birthday!🎉**")

                    with open("./lib/bot/kawaiired.0", "r", encoding="utf=8") as tf:
                        krtoken = tf.read()
                    URL = f"https://kawaii.red/api/gif/party/token={krtoken}/"
                    async with request("GET", URL, headers={}) as response:
                        jsondata = await response.json()

                        async with ClientSession() as session:
                            async with session.get(jsondata['response']) as resp:
                                data = io.BytesIO(await resp.read())
                                await channelpush.send(file=discord.File(data, 'celebrate.gif'))

                    wished = 1
                    db.execute("UPDATE birthday SET wished = ? WHERE dbid = ?", 1, i)

    @tasks.loop(minutes = 60.0)
    async def wishedreset(self):
        if datetime.now().hour < 8:
            db.execute("UPDATE birthday SET wished = ?", 0)

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("birthday")
            
async def setup(bot):
    await bot.add_cog(Birthday(bot))