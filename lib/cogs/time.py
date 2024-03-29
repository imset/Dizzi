import pytz
import discord
from discord.ext.commands import Cog, command
from discord.ext import commands
from discord import Embed, utils, app_commands, Interaction
from datetime import date
from datetime import datetime, timedelta
from pytz import timezone
from ..dizzidb import Dizzidb, dbprefix


#defines the bot's embed color
DIZZICOLOR = 0x9f4863

# copied from https://stackoverflow.com/questions/19774709/use-python-to-find-out-if-a-timezone-currently-in-daylight-savings-time
def is_dst(zonename):
    tz = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.utcnow())
    return now.astimezone(tz).dst() != timedelta(0)

class Time(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(fallback="now",
                        name="timezone",
                        aliases=["tz"],
                        brief="Get the time in HST, PST, and JST.",
                        usage="`*PREF*timezone now` - gives the current time in JST/HST/PST\n`*PREF*timezone <arg>` - Timezone conversion. `<arg>` is a time (number from 1-24) and a valid timezone. It also optionally accepts AM/PM.\nExample: `*PREF*timezone 8PM pst`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def tznow(self, ctx: commands.Context) -> None:
        """Convert a specific time in a timezone to HST, PST, and JST. There are a few timezones available to convert from, but for now it only converts to HST/PST/JST.
        
        Currently Supported Timezones:
            `[Pacific/PST/PDT]`
            `[HST/Hawaii/Honolulu]`
            `[JST/Tokyo/Japan]`
            `[BJT/China]`
            `[CST/CDT/Central]`
            `[EST/EDT/Eastern]`
            `[MST/MDT/Mountain]`
            `[PHT/Philippines/Filipino]`
            `[KST/Korea]`
        """
        utcmoment_naive = datetime.utcnow()
        utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
        localFormat = "%I:%M %p"
        hst = pytz.timezone("Pacific/Honolulu")
        pst = pytz.timezone("America/Los_Angeles")
        jst = pytz.timezone("Asia/Tokyo") 
        pst_send = utcmoment.astimezone(pst)
        hst_send = utcmoment.astimezone(hst)
        jst_send = utcmoment.astimezone(jst)
        #korea
        kst = pytz.timezone("Asia/Seoul")
        kst_send = utcmoment.astimezone(kst)
        #send timezones
        tzembed = Embed(title="Current Time", color = DIZZICOLOR)
        tzembed.add_field(name="__**HST**__", value = "> " + hst_send.strftime("%I:%M %p"), inline=True)
        tzembed.add_field(name="__**PST**__", value = "> " + pst_send.strftime("%I:%M %p"), inline=True)
        tzembed.add_field(name="__**JST**__", value = "> " + jst_send.strftime("%I:%M %p"), inline=True)
        #korea
        tzembed.add_field(name="__**KST**__", value = "> " + kst_send.strftime("%I:%M %p"), inline=True)
        await ctx.send(embed=tzembed)

    @tznow.command(brief="Convert a specific time to HST, PST, and JST.")
    @app_commands.rename(arg="time")
    async def convert(self, ctx: commands.Context, *, arg) -> None:
        #iterator variable for argument, used to determine the exact character of a string
        i = 0
        
        #initialize hour as string undefined
        hour = "undefined"
        #exception handling to make sure the string starts with a number, which will be interpreted as the hour.
        try:
            int(arg[i])
        except ValueError:
            await ctx.send("I don't understand that, sorry. Use ;help tz for command help.", ephemeral=True)
            return
        
        #check the hour
        while i <= len(arg)-1 and hour == "undefined":
            #skip any leading 0's
            if int(arg[i]) == 0:
                i += 1
                continue
            #most complicated cases are the start being 1 or 2
            elif int(arg[i]) == 1 or int(arg[i]) == 2:
                #check if there are any digits after the 1 or 2. If so, they're the hour.
                try:
                    int(arg[i+1])
                except:
                    hour = arg[i]
                    break
                else:
                    hour = arg[i] + arg[i+1]
                    if int(hour) > 24:
                        await ctx.send("Error: Hour must be between 1-24", ephemeral=True)
                        return
            
            elif int(arg[i]) >= 3:
                hour = arg[i]
                break
            else:
                await ctx.send("Error: Hour must be between 1-24", ephemeral=True)
                return
            i += 1
        
        #make sure hour is a valid number and determine AM/PM
        try:
            int(hour)
        except:
            await ctx.send("Error: Hour must be between 1-24", ephemeral=True)
            return
            
        #now for the minute and AMPM handling
        j = 0
        min = "undefined"
        #ampm
        while j <= len(arg)-1 and min == "undefined":
            if arg[j] == ":":
                try:
                    int(arg[j+1])
                    int(arg[j+2])
                except:
                    await ctx.send("Error: Minute must be a two digit number", ephemeral=True)
                    return
                else:
                    min = arg[j+1] + arg[j+2]
                    break
            j +=1
            
        #defaults min to :00    
        if min == "undefined" or int(min) >= 60:
            min = "00"
            
        #ampm handling
        ampm = "undefined"
        if "am" in arg.lower():
            ampm = "AM"
        elif "pm" in arg.lower():
            ampm = "PM"
        else:  
            if int(hour) >= 12 and int(hour) != 24:
                hour -= 12
                ampm = "PM"
            if int(hour) == 24:
                hour = 12
                ampm = "AM"
            else:
                ampm = "AM"
        
        #timezone handling
        zone = "undefined"
        if "pst" in str(arg.lower()) or "pdt" in str(arg.lower()) or "pacific" in str(arg.lower()):
            zone = "America/Los_Angeles"
            zoneshrt = "PST"
            if is_dst(zone):
                zoneshrt = "PDT"
        elif "hst" in str(arg.lower()) or "hawaii" in str(arg.lower()) or "hawai'i" in str(arg.lower()) or "honolulu" in str(arg.lower()):
            zone = "Pacific/Honolulu"
            zoneshrt = "HST"
        elif "jst" in str(arg.lower()) or "tokyo" in str(arg.lower()) or "japan" in str(arg.lower()):
            zone = "Asia/Tokyo"
            zoneshrt = "JST"
        elif "bjt" in str(arg.lower()) or "china" in str(arg.lower()):
            zone = "Asia/Shanghai"
            zoneshrt = "BJT"
        elif "cst" in str(arg.lower()) or "cdt" in str(arg.lower()) or "central" in str(arg.lower()):
            zone = "America/Chicago"
            zoneshrt = "CST"
            if is_dst(zone):
                zoneshrt = "CDT"
        elif "est" in str(arg.lower()) or "edt" in str(arg.lower()) or "eastern" in str(arg.lower()):
            zone = "America/New_York"
            zoneshrt = "EST"
            if is_dst(zone):
                zoneshrt = "EDT"
        elif "mst" in str(arg.lower()) or "mdt" in str(arg.lower()) or "mountain" in str(arg.lower()):
            zone = "America/Denver"
            zoneshrt = "MST"
            if is_dst(zone):
                zoneshrt = "MDT"
        elif "pht" in str(arg.lower()) or "philippines" in str(arg.lower()) or "filipino" in str(arg.lower()):
            zone = "Asia/Manila"
            zoneshrt = "PHT"
        elif "kst" in str(arg.lower()) or "korea" in str(arg.lower()):
            zone = "Asia/Seoul"
            zoneshrt = "KST"
        else:
            await ctx.send(f"Error: Please include a valid timezone or location indicator.", ephemeral=True)
            return

        #copied from https://stackoverflow.com/questions/18176148/converting-an-un-aware-timestamp-into-an-aware-timestamp-for-utc-conversion
        #date feature is currently not working so it always defaults to current date.
        today = date.today()
        dt = today.strftime("%m/%d/%Y") + " " + hour + ":" + min + ":00" + " " + ampm
        unaware_zone = datetime.strptime(dt, "%m/%d/%Y %I:%M:%S %p")
        localtz = timezone(zone)
        aware_zone = localtz.localize(unaware_zone)
        hst = pytz.timezone("Pacific/Honolulu")
        pst = pytz.timezone("America/Los_Angeles")
        jst = pytz.timezone("Asia/Tokyo")   
        pst_send = aware_zone.astimezone(pst)
        hst_send = aware_zone.astimezone(hst)
        jst_send = aware_zone.astimezone(jst)
        #korea
        kst = pytz.timezone("Asia/Seoul")
        kst_send = aware_zone.astimezone(kst)

        #send the timezones
        tzembed = Embed(title="Timezone Conversion: " + zone, description=hour + ":" + min + " " + ampm + " " + zoneshrt + " is:", color=DIZZICOLOR) 
        tzembed.add_field(name="__**HST**__", value = "> " + hst_send.strftime("%I:%M %p"), inline=True)
        tzembed.add_field(name="__**PST**__", value = "> " + pst_send.strftime("%I:%M %p"), inline=True)
        tzembed.add_field(name="__**JST**__", value = "> " + jst_send.strftime("%I:%M %p"), inline=True)
        #korea
        tzembed.add_field(name="__**KST**__", value = "> " + kst_send.strftime("%I:%M %p"), inline=True)
        await ctx.send(embed=tzembed)
        return

    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("time")
            
async def setup(bot):
    await bot.add_cog(Time(bot))