from discord.ext import commands
import database_connection as db
from io import BytesIO
import aiohttp
import config
import discord
from utils import Utils
import asyncio

class General:

    def __init__(self, client, cursor, auth):
        self.client = client
        self.cursor = cursor
        self.auth = auth

    @commands.cooldown(5, 60, commands.BucketType.channel)
    @commands.command(description="Says 'Pong!'",
                      brief="Says 'Pong!'",
                      help="... provided the bot is alive")
    async def ping(self):
        await self.client.say('Pong!')

    @commands.cooldown(10, 60, commands.BucketType.channel)
    @commands.command(pass_context=True,
                      help=" ...uses the inspirobot api, for more information, look into "
                           "http://inspirobot.me/api?generate=true",
                      brief='posts a randomly generated \'inspirational\' image',
                      description="Sends a file over two http requests")
    async def inspire(self, ctx):
        uri = 'http://inspirobot.me/api?generate=true'
        buffer = BytesIO()
        async with aiohttp.ClientSession() as session:
            async with session.get(uri) as resp:
                uri2 = await resp.text()
                # start a 2nd session to fetch the URI the api provided
                # lmao
                if uri2:
                    async with aiohttp.ClientSession() as session2:
                        async with session2.get(uri2) as resp2:
                            buffer = BytesIO(await resp2.read())

                await self.client.send_file(ctx.message.channel, fp=buffer, filename='inspire.jpg')
                buffer.close()

    @commands.command(pass_context=True,
                      description="Change the bot status",
                      brief="Status",
                      help="... modifies bot informations : game played")
    async def changeGame(self, ctx, game : str):
        """Change the bot status."""
        if self.auth.can(ctx.message.author, config.ADMINISTRATE_BOT):
            await self.client.change_presence(game=discord.Game(name=game))# Discord automatically shortens the game if it's too long
            print("Game succesfully changed")

    @commands.command(pass_context=True,
                      description="Change the bot status",
                      brief="Status",
                      help="... modifies bot informations : status")
    async def changeStatus(self, ctx):
        """Change the bot status"""
        if self.auth.can(ctx.message.author, config.ADMINISTRATE_BOT):
            emoji = {u"\U0001F1F4" : discord.Status.online, u"\U0001F1EE" : discord.Status.idle, u"\U0001F1E9" : discord.Status.dnd}
            choice = await Utils.emoji_vote(self.client, emoji, ctx.message)
            if choice: # choice is None if it recieved no reaction
                await self.client.change_presence(status = choice)
                print("Status successfully changed")

    @commands.command(pass_context=True,
                  description="Change the bot username",
                  brief="Username",
                  help="... modifies bot informations : username")
    async def setUsername(self, ctx, name : str):
        """Change the bot username. Limited to twice per hour by discord."""
        if self.auth.can(ctx.message.author, config.ADMINISTRATE_BOT):
            await self.client.edit_profile(username=name)
            print("Username successfully changed")

    @commands.command(pass_context=True,
                      description="Change the bot avatar",
                      brief="Avatar",
                      help="... modifies bot informations : avatar")
    async def setAvatar(self, ctx, url=None):
        """Change the bot avatar. Limited by discord ?"""
        if self.auth.can(ctx.message.author, config.ADMINISTRATE_BOT):
            if ctx.message.attachments: # Image attached to the command
                url = ctx.message.attachments[0]["url"]
            elif type(url) is str and url.startswith("http"): # Link dropped by the user
                url = url.strip()
            else:
                return print("No valid content to change the avatar")
            try: # just in case it's a wrong link -> host error ...
                with aiohttp.Timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            await self.client.edit_profile(avatar=await resp.read())
                            print("Profile picture successfully changed")
            except aiohttp.errors.ClientOSError:
                print('Something happened while trying to modify the PFP : %s' % (e))

def setup(client):
    client.add_cog(General(client, db.cursor, db.auth))
