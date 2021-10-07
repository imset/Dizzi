from discord.ext.commands import Cog
from discord.ext.commands import command
from random import choice, randint

class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @command(name="hello", aliases=["hi"])
    async def say_hello(self, ctx):
        await ctx.send(f"{choice(('Hello, ', 'Hiya, ', 'Howdy, '))} {ctx.author.mention}!")
        
    @command(name="roll", aliases=["r"])
    async def roll_dice(self, ctx, die_string: str):
        dnum, dval = (int(dice) for dice in die_string.lower().split("d"))
        rolls = [randint(1, dval) for i in range(dnum)]
        rollstr = [str(r) for r in rolls]
        
        rollsum = str(sum(rolls))
        
        i = 0
        
        while i < len(rolls):
            print("in while")
            if rolls[i] == dval:
                rollstr[i] = "**" + rollstr[i] + "**"
            else:
                rolls[i] = str(rolls[i])
            i += 1
                
        finalrollstr = " + ".join(rollstr)
        
        await ctx.send(finalrollstr + " = " + rollsum)
        
        #await ctx.send(" + ".join([str(r) for r in rolls]) + f" = {sum(rolls)}")
        
    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
            
def setup(bot):
    bot.add_cog(Fun(bot))