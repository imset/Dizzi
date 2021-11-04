from typing import Optional

from discord import Embed
from discord.utils import get
from discord.ext.commands import Cog
from discord.ext.commands import command
from discord.ext.menus import MenuPages, ListPageSource

DIZZICOLOR = 0x2c7c94

#create a list of all the commands

def syntax(command):
    cmd_and_aliases = "|".join([str(command), *command.aliases])
    params = []
    
    for key, value in command.params.items():
        if key not in ("self", "ctx"):
            params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")
            
    params = " ".join(params)
    return f"```{cmd_and_aliases} {params}```"
    
    
class HelpMenu(ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        
        super().__init__(data, per_page=5)
        
    async def write_page(self, menu, fields=[]):
        offset = (menu.current_page*self.per_page) + 1
        len_data = len(self.entries)
        
        embed = Embed(title="Dizzi's Command Help", description="What can I help you with? \n(Hint: use help <command> for more info about a specific command, or help <group> to get info about a group of commands)",color=DIZZICOLOR)
        
        embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")
        cogname = ""
        for brief, value, cog, hidden, name, enabled in fields:
            #generate cog name headers and create fields. Within Dizzi's help documents, cogs are referred to as groups.
            
            if hidden != True and enabled != False:
                if cog != cogname:
                    cogname = cog
                    embed.add_field(name="**————————————————**", value = f"**{str(cogname).title()} Group:\n————————————————**", inline=False)
                embed.add_field(name=brief, value=value, inline=False)
            else:
                continue
            
        return embed
        
    async def format_page(self, menu, entries):
        fields = []
        
        for entry in entries:
            #creates the field list that will be used in write_page to add fields
            fields.append((entry.brief or "No description", syntax(entry), entry.cog_name, entry.hidden, entry.name, entry.enabled))
            
        #sort fields list by cog_name and syntax(entry)
        fields = sorted(fields, key=lambda x: (x[2], x[4]))
        #print(fields)
        
        return await self.write_page(menu, fields)
            

class Helper(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")
        
    async def cmd_help(self, ctx, command):
        embed = Embed(title=f"Help for: `{str(command).title()}`", description=syntax(command), color=DIZZICOLOR)
        embed.add_field(name="**————————————————\nCommand Description\n————————————————**", value=f"{command.help}", inline=False)
        embed.add_field(name="**————————————————\nCommand Usage\n————————————————**", value=f"{command.usage}", inline=False)
        await ctx.send(embed=embed)
    
    @command(name="help", brief="Get help with a specific commanad", usage="`help` - gives you a list of all commands\n`help <cmd>` - gives you help documents for a `cmd`, where `cmd` is any command that Dizzi understands.\nExample: `help help` (this should look familiar)", hidden=True)
    async def show_help(self, ctx, cmd: Optional[str]):
        """What kind of person looks up help for the help command?"""
        
        #remove hidden commands
        commandlist = []
        for command in self.bot.commands:
            if command.hidden != True:
                commandlist.append(command)

        #alphabetize cmdlist by cog_name and name
        commandlist = sorted(commandlist, key=lambda x: (x.cog_name, x.name))
        
        if cmd is None:
            menu = MenuPages(source=HelpMenu(ctx, commandlist), delete_message_after=True, timeout=60.0)
            await menu.start(ctx)
            
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
                    await ctx.send("That command or command group does not exist.")
                else:
                    menu = MenuPages(source=HelpMenu(ctx, coglist), delete_message_after=True, timeout=60.0)
                    await menu.start(ctx)
    
    @show_help.error
    async def show_help_error(self, ctx, exc):
        if isinstance(exc, AttributeError):
            await ctx.send("I'm not sure what that command is. Sorry!")
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("helper")
            
def setup(bot):
    bot.add_cog(Helper(bot))