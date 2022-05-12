import re
import aiohttp
import discord
from saucenao_api import SauceNao
from typing import Optional
from discord.errors import (
    HTTPException, Forbidden
)
from discord.app_commands.errors import CommandInvokeError
from discord.ext import commands
from discord.ext.commands import (
    Cog, command, Context,
    CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown, 
    DisabledCommand, CheckFailure, max_concurrency, cooldown,
    BucketType
)
from discord import (
    Intents, Guild, channel, app_commands, Embed, File, Interaction
)

from ..db import db
from ..dizzidb import Dizzidb, dbprefix

DIZZICOLOR = 0x9f4863

#get token for saucenao
with open("./lib/cogs/searchtoken.0", "r", encoding="utf=8") as tf:
    SAUCETOKEN = tf.read()


def get_attrs(klass):
    return [k for k in klass.__dict__.keys()
            if not k.startswith('__')
            and not k.endswith('__')]

#request function for saucenao
def sauce_request(url) -> dict:
    sauce = SauceNao(api_key=SAUCETOKEN)
    results = sauce.from_url(url)
    best = results[0]

    vallist = []
    keylist = []
    reqdict = {}

    if bool(results):
        for i in dir(results[0]):
            if not str(i).startswith("_"):
                reqdict[str(i)] = i
                keylist.append(str(i))
                vallist.append(i)

    print 

    if bool(results):
        for i in get_attrs(best):
            #print(best.i)
            pass
        reqdict = dict(zip(keylist, vallist))

    reqdict = {
        "number": len(results),
        "bool": bool(results),
        "thumb": best.thumbnail,
        "similarity": best.similarity,
        "title": best.title,
        "url": best.urls,
        "author": best.author
    }

    return reqdict

#get img url in other ways if not provided
async def get_imgurl(ctx):
    try:
        #try replied message first
        message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except:
        #if no replied message, just take the whole message
        message = ctx.message

  #find message attachments
    if len(message.attachments) > 0:
        attachment = message.attachments[0]
        if attachment.filename.endswith(".jpg") or attachment.filename.endswith(".jpeg") or attachment.filename.endswith(".png") or attachment.filename.endswith(".webp") or attachment.filename.endswith(".gif"):
            imgurl = attachment.url
        else:
            await ctx.send("I don't understand that image, sorry!")
            return
    else:
        #no message attachment, find url
        # thanks to https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
        attachment = re.findall(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})',
                                message.content)[0]
        if len(attachment) == 0:
            await ctx.send("To search you must either include an image, an image url, or reply to a message with an image in it.")
            return
        elif attachment.endswith(".jpg") or attachment.endswith(".jpeg") or attachment.endswith(".png") or attachment.endswith(".webp") or attachment.endswith(".gif"):
            imgurl = attachment
        else:
            await ctx.send("I don't understand that image, sorry!")
            return

    return imgurl

class Search(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="sauce",
                        aliases=['s'],
                        brief="Reverse image lookup, specialized for anime or manga.",
                        usage="`*PREF*sauce anime <img>` - Searches `<img>` on trace.moe. `<img>` can be an image url, an image uploaded with the command, or a replied image.\n"
                            "Example: `*PREF*sauce anime https://i.imgur.com/zmXLgvW.gif`\n\n"
                            "`*PREF*sauce other <img>` - Searches `<img>` on SauceNao. `<img>` can be an image url, an image uploaded with the command, or a replied image.\n"
                            "Example: `*PREF*sauce other https://i.imgur.com/zmXLgvW.gif`")
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def sauce(self, ctx, img: Optional[str]):
        """
        Reverse image lookup powered by SauceNao or Trace.Moe.
        Has two subcommands: ``anime`` for anime searching, and ``other`` for anything besides anime (manga, fanart, etc.)
        Note: usage limitations require that you can only use each subcommand a limited number of times per day (currently 10).
        Also, if invoked via ``/``, ``sauce`` will only function with image urls, not through replies or uploaded images.
        """
        await ctx.send(f"Sorry, the syntax for this command has changed.\nInstead of ``{dbprefix(ctx.guild)}sauce <img>`` or ``{dbprefix(ctx.guild)}anisauce <img>``, you now need to use ``{dbprefix(ctx.guild)}sauce anime <img>`` or ``{dbprefix(ctx.guild)}sauce other <img>`` (notice the space).\nThis command can also be invoked with ``/`` instead of {dbprefix(ctx.guild)}.")

    @sauce.command(name="anime",
            #aliases=["anisauce", "as"],
            brief="Highly detailed reverse lookup specifically for anime, powered by trace.moe",
            usage="`*PREF*anisource <img>` - Searches `<img>` on trace.moe. `<img>` can be an image url, an image uploaded with the command, or a replied image.\n"
            "Example: `*PREF*anisource https://i.imgur.com/zmXLgvW.gif`")
    @app_commands.rename(img="image_url")
    @app_commands.checks.cooldown(10, 86400, key=lambda i: (i.guild_id, i.user.id))
    @max_concurrency(1, per=BucketType.default, wait=True)
    async def anisource(self, ctx, img = None):
        """
        Search an anime picture on Trace.moe, and get back the source and its video context.
        Note: trace.moe usage limitations require that you can only use this command a limited number of times per day (currently 10).
        """

        pref = dbprefix(ctx.guild)

        if img is None:
            img = await get_imgurl(ctx)

        sourceurl = f"https://api.trace.moe/search?cutBorders&url={img}"
        
        async with aiohttp.request("GET", sourceurl, headers={}) as response:
            if response.status == 200:
                data = await response.json()
                tmresult = data["result"][0]

                tmtitle = tmresult["filename"]
                tmsimi = tmresult["similarity"]
                tmvideo = tmresult["video"]
                if len(tmvideo) > 250:
                    tmvideo = "[Video URL too long]"
                tmimage = tmresult["image"]
                tmepi = tmresult["episode"]

                embed = Embed(title=f"Best Guess: {tmtitle}", description=f"Input URL: {img}\nEpisode: {tmepi}", color=DIZZICOLOR)
                embed.add_field(name=f"Video: {tmvideo}", value=f"Similarity: {tmsimi}")
                embed.set_thumbnail(url=tmimage)
                embed.add_field(name="Note:", value="Because of limitations with the free version of Trace.moe, you can only use this command 10x per 24hr period.", inline=False)
                embed.set_footer(text=f"This tool does not work well with edited/cropped images.")
                await ctx.send(embed=embed)

            elif response.status == 402:
                await ctx.send(f"Dizzi has maxed out on its monthly alotted searches with Trace.Moe. Try using {pref}source / {pref}s to search instead.", ephemeral=True)
            else:
                await ctx.send(f"API returned a {response.status} status.", ephemeral=True)

    @sauce.command(name="other",
            #aliases=["sauce", "s"],
            brief="More general reverse image lookup for anime/manga/fanart, powered by SauceNao",
            usage="`*PREF*anisource <img>` - Searches `<img>` on SauceNao. `<img>` can be an image url, an image uploaded with the command, or a replied image.\n"
            "Example: `*PREF*source https://i.imgur.com/zmXLgvW.gif`")
    @app_commands.rename(img="image_url")
    @app_commands.checks.cooldown(10, 86400, key=lambda i: (i.guild_id, i.user.id))
    @max_concurrency(1, per=BucketType.default, wait=True)
    async def othersource(self, ctx, img = None):
        """
        Search a picture on SauceNao, and get back the closest match to its source.
        If you have a screenshot from an anime, you can also use ;as to use the more powerful Trace.moe search.
        Note: trace.moe usage limitations require that you can only use this command a limited number of times per day (currently 10).
        """

        pref = dbprefix(ctx.guild)

        #a lot of this is taken from https://stackoverflow.com/questions/66858220/how-do-you-get-the-image-from-message-and-display-it-in-an-embed-discord-py
        if img is None:
            img = await get_imgurl(ctx)

        saucedict = sauce_request(img)

        if saucedict == {}:
            await ctx.send(f"SauceNao couldn't find anything on that image. Sorry!", ephemeral=True)
            return
        else:
            saucetitle = saucedict["title"]
            #holy shit this is awful
            try:
                sauceurl = saucedict["url"][0]
            except:
                sauceurl = ""
            try:
                sauceauthor = saucedict["author"]
            except:
                sauceauthor = ""
            saucesimi = saucedict["similarity"]
            embed = Embed(title=f"Best Guess: {saucetitle}", description=f"Input URL: {img}", color=DIZZICOLOR)
            if sauceurl != "":
                embed.add_field(title=f"Link to Sauce: {sauceurl}")
            embed.add_field(name=f"Author: {sauceauthor}", value=f"Similarity: {saucesimi}")
            embed.set_thumbnail(url=saucedict["thumb"])
            embed.add_field(name="Note:", value="Because of limitations with the free version of SauceNao, you can only use this command 10x per 24hr period.",
                            inline=False)
            embed.set_footer(text=f"This tool does not work well with edited/cropped images.\nSearching for an anime? Try ``{pref}sauce anime`` ``/sauce anime`` for a more detailed search.")

            await ctx.send(embed=embed)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("search")

async def setup(bot):
  await bot.add_cog(Search(bot))