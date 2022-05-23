import asyncio

from lib.bot import bot
VERSION = "2.0.0"

asyncio.run(bot.run(VERSION))