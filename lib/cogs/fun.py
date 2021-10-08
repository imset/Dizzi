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
    async def roll_dice(self, ctx, *, die_string: str):      
        dnum, dval = (dice for dice in die_string.lower().split("d"))
        dnum = int(dnum)
        
        if "+" in dval:
            dval, dbns = (int(dice) for dice in dval.lower().split("+"))
        else:
            dbns = 0
            dval = int(dval)
        
        if dnum > 100 or dval > 100 or dbns > 100:
            await ctx.send("Error: please limit sides/rolls/bonus to 100 max.")
            return
            
        rolls = [randint(1, dval) for i in range(dnum)]
        rollstr = [str(r) for r in rolls]
        
        i = 0
        
        while i < len(rolls):
            if rolls[i] == dval:
                rollstr[i] = "**" + rollstr[i] + "**"
            else:
                #rolls[i] = str(rolls[i])
                pass
            i += 1
        '''
        if dbns == 0:

        else:
            finalrollstr = " + ".join(rollstr) + " + __*" + str(dbns) + "*__"
            rollsum = sum(rolls)
            rollsum += dbns
        '''
        finalrollstr = " + ".join(rollstr)
        rollsum = sum(rolls)
        if dbns == 0:
            await ctx.send(finalrollstr + " = " + str(rollsum))
        else:
            await ctx.send(finalrollstr + " = " + str(rollsum) + " + *" + str(dbns) + "* = __**" + str(rollsum + dbns) + "**__")
                
    @Cog.listener()
    async def on_ready(self):
        #tells bot that the cog is ready
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
            
def setup(bot):
    bot.add_cog(Fun(bot))