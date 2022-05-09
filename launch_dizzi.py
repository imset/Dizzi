import asyncio

from lib.bot import bot
VERSION = "1.1.0"

asyncio.run(bot.run(VERSION))