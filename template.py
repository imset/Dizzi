#Imports discord.py bot library
import discord

#creates an instance of a client
client = discord.Client()

#each client event uses a different decorator
@client.event
#on_ready occurs when the bot finishes logging in
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
#on_message happens every time a message is received. 
async def on_message(message):
    #makes sure the bot ignores its own messages
    if message.author == client.user:
        return
    #check if message starts with $hello, if so it replies.
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
#runs the bot with the necessary login token
client.run('your token here')