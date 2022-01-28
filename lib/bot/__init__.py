from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from glob import glob

from discord import Intents, Embed, File, Game, Activity, ActivityType
from discord.ext.commands import (
    Bot as BotBase, CommandNotFound, BadArgument, MissingRequiredArgument, 
    CommandOnCooldown, DisabledCommand, CheckFailure, Context, when_mentioned_or, 
    command, has_permissions
)
from discord.errors import (
    HTTPException, Forbidden
)
#from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, DisabledCommand, CheckFailure
#from discord.ext.commands import Context
#from discord.ext.commands import when_mentioned_or, command, has_permissions

#IF SOMETHING'S BROKEN IT'S PROBABLY HERE from discord.ext import commands
#import discord
#from discord import Embed, File

import logging
from ..db import db
from ..dizzidb import dbsetup

#the following is cut and paste from the library tutorial for logging, outputs dizzilog.log

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='dizzilog.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

OWNER_IDS = [134760463811477504]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]
#exceptions that will be ignored
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument, DisabledCommand)

#gets the set prefix for the bot, see settings cog
def get_prefix(bot, message):
    prefix = db.field("SELECT Prefix FROM guildsettings WHERE GuildID = ?", message.guild.id)
    return when_mentioned_or(prefix)(bot, message)

class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)
            
    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f" {cog} cog ready")
        
    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        
        self.scheduler = AsyncIOScheduler()
        
        db.autosave(self.scheduler)
        
        super().__init__(
            command_prefix=get_prefix,
            owner_ids=OWNER_IDS,
            intents=Intents.all(),
            activity=Game(name=";help")
        )
    
    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f" {cog} cog loaded")
        print(" cog setup complete")
        
    def run(self, version):
        self.VERSION = version
        
        print("Running Cog Setup...")
        self.setup()
        
        with open("./lib/bot/token.0", "r", encoding="utf=8") as tf:
            self.TOKEN = tf.read()
            
        print("Running Dizzi...")
        super().run(self.TOKEN, reconnect=True)
        
    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)
        
        #apparently to avoid sending commands over dm
        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                await ctx.send("Please wait a moment before sending a command. I'm still waking up.")
        
        
        
    async def on_connect(self):
        print (" Dizzi logged in as {0.user}".format(bot))
        
    async def on_disconnect(self):
        print("Dizzi Disconnected")
        
    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            #await args[0].send("Something went wrong.")
            await args[0].message.add_reaction("❌")
        raise
    
    #do not change on_command_error from passing on CommandNotFound
    async def on_command_error(self, ctx, exc):
        if any([isinstance(exc, CommandNotFound) for error in IGNORE_EXCEPTIONS]):
            pass

        elif isinstance(exc, DisabledCommand):
            pass
            
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing")
            
        elif isinstance(exc, CommandOnCooldown):
            print("Command Cooldown Hit")
            retry = exc.retry_after
            if retry < 60:
                print("Seconds")
                await ctx.send(f"Cool it! Try again in {retry:,.2f} seconds.")
            elif (retry/60) < 60:
                print("minutes")
                await ctx.send(f"Cool it! Try again in {(retry/60):,.2f} minutes.")
            elif (retry/360) < 24:
                print("hours")
                await ctx.send(f"Cool it! Try again in {(retry/360):,.2f} hours.")
            
        elif isinstance(exc, CheckFailure):
            await ctx.send("Hey! You don't have permission to do that!")
            
        elif hasattr(exc, "original"):
            if isinstance(exc.original, Forbidden):
                await ctx.send("I do not have permission to do that!")
            else:
                raise exc.original
                
        else:
            raise exc
    
    async def on_ready(self):
        if not self.ready:
            self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await sleep(3)
                
            self.ready = True
            print("Dizzi is ready")
            
        else:
            print("Dizzi reconnected")
        
    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)


    #events for when the bot joins a guild
    #currently this is not needed since the reaction database adds and updates automatically.
    '''
    async def on_guild_join(self, guild):
        print(f"Joined guild {guild.name} ({guild.id}). Adding members to database...")
        dbsetup(guild)
    '''


bot = Bot()