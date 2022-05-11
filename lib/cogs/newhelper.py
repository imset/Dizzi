from typing import Optional
import discord
from discord import Embed, app_commands, Interaction
from discord.utils import get
from discord.ext.commands import (
    Cog, command, guild_only
)
from discord.ext.menus import (
    MenuPages, ListPageSource
)
from discord.ext import menus, commands
from discord.ext.menus.views import ViewMenuPages

from ..db import db
from ..dizzidb import dbprefix

DIZZICOLOR = 0x9f4863

#create a list of all the commands

def syntax(command, guild):
    cmd_and_aliases = dbprefix(guild) + "|".join([str(command), *command.aliases])
    params = []
    
    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")
            
    params = " ".join(params)
    return f"```{cmd_and_aliases} {params}```"
    
    
class HelpMenu(ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        
        super().__init__(data, per_page=8)
        
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
            
            if hidden != True and enabled != False and name != "help":
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
        embed = Embed(title=f"Help for: `{str(command).title()}`", description=syntax(command, ctx.guild), color=DIZZICOLOR)
        embed.add_field(name="**————————————————\nCommand Description\n————————————————**", value=f"{command.help}", inline=False)
        #the following is used to replace *PREF* in usage docs with the actual prefix
        tmpusage = command.usage.replace("*PREF*", dbprefix(ctx.guild))
        embed.add_field(name="**————————————————\nCommand Usage\n————————————————**", value=f"{tmpusage}", inline=False)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="help",
            brief="Get help with a specific command",
            usage="`*PREF*help` - gives you a list of all commands\n`{dbprefix(ctx.guild)}help <cmd>` - gives you help documents for a `<cmd>`, where `<cmd>` is any command that Dizzi understands.\nExample: `*PREF*help help` (this should look familiar)")
    @app_commands.rename(cmd="command")
    @app_commands.guild_only()
    #@app_commands.guilds(discord.Object(762125363937411132))
    async def show_newhelp(self, ctx, cmd: Optional[str]):
        """What kind of person looks up help for the help command?"""
        if ctx.message.guild == None:
            await ctx.send("Sorry, there's a bug right now that prevents me from sending help commands over DM. For now, try using that command in a server we're in together!")
            return
            
        #remove hidden commands
        commandlist = []
        for command in self.bot.commands:
            if command.hidden != True:
                commandlist.append(command)

        #alphabetize cmdlist by cog_name and name
        commandlist = sorted(commandlist, key=lambda x: (x.cog_name, x.name))
        
        if cmd is None:
            menu = ViewMenuPages(source=HelpMenu(ctx, commandlist), delete_message_after=True, timeout=60.0)
            await menu.start(ctx)
            if ctx.interaction is not None:
                await ctx.interaction.response.send_message(f"Success: Retrieved Help Docs", ephemeral=True)
            
        else:
            if (commandinput := get(self.bot.commands, name=cmd)):
                await self.cmd_help(ctx, commandinput)
            #checks for aliases
            elif (self.bot.get_command(cmd) != None):
                commandalias = str(self.bot.get_command(cmd))
                command = get(self.bot.commands, name=commandalias)
                await self.cmd_help(ctx, command)
            else:
                #check cogs
                coghelpbool = False
                #creates a smaller list of commands that have a cog that match the input
                coglist = [x for x in commandlist if cmd.title() == x.cog_name]
                
                #if the coglist is empty, search fails
                if not len(coglist):    
                    await ctx.send(f"That command or command group does not exist ({cmd}). Use /help or {dbprefix(ctx.guild)}help for a list of commands.", ephemeral=True)
                else:
                    menu = ViewMenuPages(source=HelpMenu(ctx, coglist))
                    await menu.start(ctx)
                    if ctx.interaction is not None:
                        await ctx.interaction.response.send_message(f"Success: Retrieved Help Docs for {cmd}", ephemeral=True)
    @show_newhelp.error
    async def show_newhelp_error(self, ctx, exc):
        if isinstance(exc, AttributeError):
            await ctx.send("I'm not sure what that command is. Sorry!", ephemeral=True)
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("newhelper")
            
async def setup(bot):
    await bot.add_cog(NewHelper(bot))