#Imports discord.py bot library
import discord
from discord.ext import commands
#for timezone handling
from datetime import date
from datetime import datetime
import pytz
from pytz import timezone
#the following is cut and paste from the library tutorial for logging, outputs dizzilog.log
import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='dizzilog.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#creates an instance of a client, command prefix is ;
client = commands.Bot(command_prefix=';')

#repeat command to test with
@client.command()
async def rep(ctx, *, arg):
    await ctx.send(arg)
    
#the big timezone boy itself

@client.command()
async def tz(ctx, *, arg):

    #first thing, make sure that arg is not "now"
    if arg != "now" and arg != "help":
        #first we want to parse through the arg for the first number. If it's a 0, skip ahead to the next character. If it's a 1 or 2, check if the next character is a :, and if not, concat with the next character.
        i = 0
        
        #determine relevant hour
        hour = "undefined"
        #exception handling to make sure the string starts with a number, which is interpreted as the hour.
        try:
            int(arg[i])
        except ValueError:
            await ctx.send("I don't understand that, sorry")
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
                    #isinstance(arg[i+1],int)
                    int(arg[i+1])
                except:
                    hour = arg[i]
                    break
                else:
                    hour = arg[i] + arg[i+1]
                    if int(hour) > 24:
                        await ctx.send("Error: Hour must be between 1-24")
                        return

            elif int(arg[i]) >= 3:
                hour = arg[i]
                break
            else:
                await ctx.send("Error: Hour must be between 1-24")
                return
            i += 1
        
        #make sure hour is a valid number and determine AM/PM
        try:
            int(hour)
        except:
            await ctx.send("Error: Hour must be between 1-24")
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
                    await ctx.send("Error: Minute must be a two digit number")
                    return
                else:
                    min = arg[j+1] + arg[j+2]
                    break
            '''
            elif arg[j] == "a" or arg[j] == "A":
                min = "00"
                ampm = "AM"
                break
            elif arg[j] == "p" or arg[j] == "P":
                min = "00"
                ampm = "PM"
                break
            '''
            j +=1
            
        #defaults min to :00    
        if min == "undefined" or int(min) >= 60:
            print("Cannot find minutes or minutes too large. Defaulting to :00.")
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
        if "pst" in str(arg.lower()) or "pdt" in str(arg.lower()):
            zone = "America/Los_Angeles"
        elif "hst" in str(arg.lower()):
            zone = "Pacific/Honolulu"
        elif "jst" in str(arg.lower()):
            zone = "Asia/Tokyo"
        else:
            await ctx.send("Error: Please include a valid timezone (PST/HST/JST)")
            return

        #copied from https://stackoverflow.com/questions/18176148/converting-an-un-aware-timestamp-into-an-aware-timestamp-for-utc-conversion
        #date feature is currently not working so it always defaults to current date.
        today = date.today()
        dt = today.strftime("%m/%d/%Y") + " " + hour + ":" + min + ":00" + " " + ampm
        unaware_zone = datetime.strptime(dt, "%m/%d/%Y %I:%M:%S %p")
        localtz = timezone(zone)
        aware_zone = localtz.localize(unaware_zone)
        #utc will hold the data for all 3 timezones
        #utc = aware_zone.astimezone(pytz.utc)
        hst = pytz.timezone("Pacific/Honolulu")
        pst = pytz.timezone("America/Los_Angeles")
        jst = pytz.timezone("Asia/Tokyo")   
        pst_send = aware_zone.astimezone(pst)
        hst_send = aware_zone.astimezone(hst)
        jst_send = aware_zone.astimezone(jst)
        #send the 3 timezones
        await ctx.send("**HST**: " + hst_send.strftime("%I:%M %p") + "\n**PST**: " + pst_send.strftime("%I:%M %p") + "\n**JST**: " + jst_send.strftime("%I:%M %p"))
        return
    #if arg is "now". copied from https://stackoverflow.com/questions/10997577/python-timezone-conversion
    elif arg == "now":
        utcmoment_naive = datetime.utcnow()
        utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
        localFormat = "%I:%M %p"
        hst = pytz.timezone("Pacific/Honolulu")
        pst = pytz.timezone("America/Los_Angeles")
        jst = pytz.timezone("Asia/Tokyo") 
        pst_send = utcmoment.astimezone(pst)
        hst_send = utcmoment.astimezone(hst)
        jst_send = utcmoment.astimezone(jst)
        #send the 3 timezones
        await ctx.send("**HST**: " + hst_send.strftime("%I:%M %p") + "\n**PST**: " + pst_send.strftime("%I:%M %p") + "\n**JST**: " + jst_send.strftime("%I:%M %p"))
    else:
        await ctx.send("Timezone conversion for HST/PST/JST. Will reply with a given time in all 3 time zones. \n__**Format:**__\n*Current Time:* **;tz now**\n*Timezone Conversion:* **;tz [time] [AM/PM (optional)] [timezone (PST/HST/JST)]**")

#reports that client has connected
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

#runs the bot with the necessary login token

client.run('NTg4NTg3NDc4OTcwMjY5NzE3.XQHSzg.wqkViUp6RAc13GHwY5M-XkEG_PU')