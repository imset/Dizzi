from typing import Optional, List
import math
import discord
import textdistance
from discord import Embed, app_commands, Interaction
from discord.utils import get
from discord.ext.commands import (
    Cog, command, guild_only
)
from discord.app_commands.errors import CommandInvokeError
from discord.ext.menus import (
    MenuPages, ListPageSource
)
from discord.ext import menus, commands
from discord.ext.menus.views import ViewMenuPages

from ..db import db
from ..dizzidb import dbprefix

DIZZICOLOR = 0x9f4863

#create a list of all the commands

def syntax(command, guild, single = False):
    #single is used to determine if help is being invoked for the whole list or just a single command

    if guild != None:
        cmd_and_aliases = dbprefix(guild) + "|".join([str(command), *command.aliases])
    else:
        cmd_and_aliases = "!" + "|".join([str(command), *command.aliases])

    try:
        if command.with_app_command == True:
            slash_txt = "/" + str(command)
            noapp = False
        else:
            slash_txt == ""
            noapp = True

    except AttributeError:
        slash_txt = ""
        noapp = True
        pass

    params = []
    
    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")
            
    params = " ".join(params)


    if single == False:
        return f"```{cmd_and_aliases} {params}```"
    elif noapp == True and single == True:
        return f"This command can only be run as a **text command**.\n```{cmd_and_aliases} {params}```"
    else:
        return f"This command can be run either as a **text command** or a **slash command**.\n\n`Text:`\n```{cmd_and_aliases} {params}```\n`Slash:`\n```{slash_txt} {params}```"

def levdist(self, data, type):
    data = data.lower()
    if type == "command":
        #get command list ignoring hidden commands
        commandlist = []
        for command in self.bot.commands:
            if command.hidden != True and command.name != "help" and command.name != "jishaku":
                commandlist.append(command)

        simlist = []
        for cmd in commandlist:
            simlist.append(textdistance.damerau_levenshtein.normalized_similarity(data, cmd.name.lower()))

        #thanks to: https://stackoverflow.com/questions/2474015/getting-the-index-of-the-returned-max-or-min-item-using-max-min-on-a-list
        index_max = max(range(len(simlist)), key=simlist.__getitem__)


        if max(simlist) >= 0.7:
            return commandlist[index_max].name
        else:
            return None

    elif type == "cog":
        #get command list ignoring hidden commands
        commandlist = []
        for command in self.bot.commands:
            if command.hidden != True and command.name != "help" and command.name != "jishaku":
                commandlist.append(command)

        #create full list of cogs
        cogset = set()
        for cmd in commandlist:
            cogset.add(cmd.cog_name.lower())

        simlist = []
        coglist = []
        #compare input to cog list
        for cog in cogset:
            simlist.append(textdistance.damerau_levenshtein.normalized_similarity(data, cog))
            coglist.append(cog)


        #thanks to: https://stackoverflow.com/questions/2474015/getting-the-index-of-the-returned-max-or-min-item-using-max-min-on-a-list
        index_max = max(range(len(simlist)), key=simlist.__getitem__)

        # print(coglist[index_max])
        # print(max(simlist))

        if max(simlist) >= 0.7:
            return coglist[index_max]
        else:
            return None
    
    
class HelpMenu(ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        
        super().__init__(data, per_page=6)
        
    async def write_page(self, menu, fields=[]):
        offset = (menu.current_page*self.per_page) + 1
        len_data = len(self.entries)
        
        embed = Embed(title="Dizzi's Command Help", description=f"Use ``/help <command>`` or ``{dbprefix(self.ctx.guild)}help <command>`` for more info about a specific command\n Most commands can be invoked with either ``/``, ``{dbprefix(self.ctx.guild)}``, or by pinging Dizzi directly. While the ``/`` version of commands are recommended, commands will be displayed with the ``{dbprefix(self.ctx.guild)}`` prefix in the help docs for consistency. ",color=DIZZICOLOR)
        
        #embed.set_thumbnail(url=self.ctx.guild.me.avatar)
        embed.set_thumbnail(url=self.ctx.me.avatar)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")
        cogname = ""
        for brief, value, cog, hidden, name, enabled in fields:
            #generate cog name headers and create fields. Within Dizzi's help documents, cogs are referred to as groups.
            
            if hidden != True and enabled != False and name != "help" and name != "jishaku":
                if cog != cogname:
                    cogname = cog
                    embed.add_field(name="**————————————————**", value = f"**{str(cogname).title()} Commands:\n————————————————**", inline=False)
                embed.add_field(name=brief, value=value, inline=False)
            else:
                continue
            
        return embed
        
    async def format_page(self, menu, entries):
        fields = []
        
        for entry in entries:
            #creates the field list that will be used in write_page to add fields
            fields.append((entry.brief or "No description", syntax(entry, self.ctx.guild), entry.cog_name, entry.hidden, entry.name, entry.enabled))
            
        #sort fields list by cog_name and syntax(entry)
        fields = sorted(fields, key=lambda x: (x[2], x[4]))
        #print(fields)
        
        return await self.write_page(menu, fields)
            

class NewHelper(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")
        
    async def cmd_help(self, ctx, command):
        embed = Embed(title=f"Help for: `{str(command).title()}`", description=syntax(command, ctx.guild, single = True), color=DIZZICOLOR)
        embed.add_field(name="**————————————————\nCommand Description\n————————————————**", value=f"{command.help}", inline=False)
        #the following is used to replace *PREF* in usage docs with the actual prefix
        tmpusage = command.usage.replace("*PREF*", dbprefix(ctx.guild))
        embed.add_field(name="**————————————————\nCommand Usage\n————————————————**", value=f"{tmpusage}", inline=False)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="help",
            brief="View a list of all commands, or get help with a specific command",
            usage=f"`*PREF*help` - gives you a list of all commands\n`*PREF*help <cmd>` - gives you help documents for a `<cmd>`, where `<cmd>` is any command that Dizzi understands.\nExample: `*PREF*help help` (this should look familiar)")
    @app_commands.rename(cmd="command")
    #@app_commands.guild_only()
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def show_help(self, ctx, cmd: Optional[str]):
        """What kind of person looks up help for the help command?"""
        if ctx.interaction is not None:
            await ctx.interaction.response.defer()
        #remove hidden commands
        commandlist = []
        for command in self.bot.commands:
            if command.hidden != True and command.name != "help" and command.name != "jishaku":
                commandlist.append(command)

        #alphabetize cmdlist by cog_name and name
        commandlist = sorted(commandlist, key=lambda x: (x.cog_name, x.name))

        #if the help command is called in a DM, there's various errors. This handles it.
        if ctx.message.guild == None and (cmd is None or cmd.lower() == "all" or cmd.lower() == "dizzi" or cmd.lower() == "jishaku" or cmd.lower() == "jsk"):
            # await ctx.send("Sorry, there's a bug right now that prevents me from sending help commands over DM. For now, try using that command in a server we're in together!")
            # return
            fields = []
            for entry in commandlist:
                #Todo: Make this a function and call it in format_page
                fields.append((entry.brief or "No description", syntax(entry, ctx.guild), entry.cog_name, entry.hidden, entry.name, entry.enabled))
            #stuff to split the command
            cmdsnum = len(commandlist)
            cmdsend = []
            msgs = int(math.ceil(cmdsnum / 15))
            fields = sorted(fields, key=lambda x: (x[2], x[4]))
            i = 0
            while i < msgs:
                if i == 0:
                    embed = Embed(title="Dizzi's Command Help", description=f"Use ``/help <command>`` or ``!help <command>`` for more info about a specific command\n Most commands can be invoked with either ``/``, ``!``, or by pinging Dizzi directly. While the ``/`` version of commands are recommended, commands will be displayed with the ``!`` prefix in the help docs for consistency.",color=DIZZICOLOR)
                else:
                    embed = Embed(title=f"Dizzi's Command Help (Page {i+1})", color=DIZZICOLOR)
                embed.set_thumbnail(url=ctx.me.avatar)
                #embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")
                cogname = ""
                for brief, value, cog, hidden, name, enabled in fields[i*15:(i+1)*15]:
                    #generate cog name headers and create fields. Within Dizzi's help documents, cogs are referred to as groups.
                    if hidden != True and enabled != False and name != "help" and name != "jishaku":
                        if cog != cogname:
                            cogname = cog
                            embed.add_field(name="**————————————————**", value = f"**{str(cogname).title()} Commands:\n————————————————**", inline=False)
                        embed.add_field(name=brief, value=value, inline=False)
                    else:
                        continue
                cmdsend.append(embed)
                i += 1

            for i in range(msgs):
                await ctx.send(embed=cmdsend[i])

        elif cmd is None or cmd.lower() == "all" or cmd.lower() == "dizzi" or cmd.lower() == "jishaku" or cmd.lower() == "jsk":
            menu = ViewMenuPages(source=HelpMenu(ctx, commandlist), delete_message_after=True, timeout=60.0)
            #used to fix some bug in the menu helper
            try:
                await menu.start(ctx)
            except AttributeError:
                pass

            if ctx.interaction is not None:
                #await ctx.interaction.followup.send(f"Success: Retrieved Help Docs", ephemeral=True)
                await ctx.send("Success: Retrieved Help Docs", ephemeral=True)
            
        else:
            if (commandinput := get(self.bot.commands, name=cmd)):
                await self.cmd_help(ctx, commandinput)
            #checks for aliases
            elif (self.bot.get_command(cmd) != None):
                commandalias = str(self.bot.get_command(cmd))
                command = get(self.bot.commands, name=commandalias)
                await self.cmd_help(ctx, command)
            #check if option is a cog. Looks scary but makes sense if you think about it.
            elif len(coglist := [x for x in commandlist if cmd.title() == x.cog_name]) != 0:
                menu = ViewMenuPages(source=HelpMenu(ctx, coglist))
                await menu.start(ctx)
                if ctx.interaction is not None:
                    await ctx.send(f"Success: Retrieved Help Docs for {cmd}", ephemeral=True)
            #check lev distance for commands
            elif (cmdchk := levdist(self, data=cmd, type="command")) != None:
                cmd = cmdchk
                commandinput = get(self.bot.commands, name=cmd)
                await self.cmd_help(ctx, commandinput)
            #check lev distance for cogs (this is dummy hard so I'm coming back to it later)
            elif (cogchk := levdist(self, data=cmd, type="cog")) != None:
                cmd = cogchk
                coglist = [x for x in commandlist if cmd.title() == x.cog_name]
                menu = ViewMenuPages(source=HelpMenu(ctx, coglist))
                await menu.start(ctx)
                if ctx.interaction is not None:
                    await ctx.send(f"Success: Retrieved Help Docs for {cmd}", ephemeral=True)
            else:
                 await ctx.send(f"That command or command group does not exist ({cmd}). Use /help or {dbprefix(ctx.guild)}help for a list of commands.", ephemeral=True)

    #autocomplete for help commands
    @show_help.autocomplete('cmd')
    async def show_help_autocomplete(self, interaction: commands.Context, current: Optional[str]) -> List[app_commands.Choice[str]]:
        #used to make sure the help command matches properly with the beginning of strings
        curlen = len(current)
        return [
            app_commands.Choice(name=command, value=command)
            for command in self.bot.commandnameslist if current.lower() in command.lower()[:curlen]
        ][:25]

    @show_help.error
    async def show_help_error(self, ctx, exc):
        if isinstance(exc, AttributeError):
            await ctx.send("I'm not sure what that command is. Sorry!", ephemeral=True)
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("newhelper")
            # #setup all command names
            #this is now located in  /bot/__init__.py
            # self.commandnameslist = []
            # for command in self.bot.commands:
            #     if command.hidden != True and command.name != "help" and command.name != "jishaku":
            #         self.commandnameslist.append(command.name)
            # self.commandnameslist.sort()
            
async def setup(bot):
    await bot.add_cog(NewHelper(bot))