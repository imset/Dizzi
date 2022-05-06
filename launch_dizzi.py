import asyncio

from lib.bot import bot
VERSION = "0.2.0"

asyncio.run(bot.run(VERSION))