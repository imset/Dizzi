from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound
from discord import Intents
from glob import glob

from ..db import db

import discord
from discord.ext import commands
from discord import Embed, File

#the following is cut and paste from the library tutorial for logging, outputs dizzilog.log
import logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='dizzilog.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

PREFIX = ";"
OWNER_IDS = [134760463811477504]
COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]

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
        self.prefix = PREFIX
        self.ready = False
        self.cogs_ready = Ready()
        
        self.scheduler = AsyncIOScheduler()
        
        db.autosave(self.scheduler)
        
        super().__init__(
            command_prefix=PREFIX,
            owner_ids=OWNER_IDS,
            intents=Intents.all()
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
        
    async def on_connect(self):
        print (" Dizzi logged in as {0.user}".format(bot))
        
    async def on_disconnect(self):
        print("Dizzi Disconnected")
        
    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
        raise
    
    #do not change on_command_error from passing on CommandNotFound
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, CommandNotFound):
            pass
        elif hasattr(exc, "original"):
            raise exc.original
        else:
            raise exc
    
    async def on_ready(self):
        if not self.ready:
            self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)
                
            self.ready = True
            print("Dizzi is ready")
            
        else:
            print("Dizzi reconnected")
        
    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

bot = Bot()