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
        if self.auth.can(ctx.message.author, config.DEBUG):
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
    async def changeGame(self, ctx):
        """Change the bot status."""
        if self.auth.can(ctx.message.author, config.BOT_INFO):
            args = Utils.parse_message_content(ctx)
            game=discord.Game(name=args["message"]) # Discord automatically shortens the game if it's too long
            await self.client.change_presence(game=game)
            print("Game succesfully changed")

    @commands.command(pass_context=True,
                      description="Change the bot status",
                      brief="Status",
                      help="... modifies bot informations : status")
    async def changeStatus(self, ctx):
        """Change the bot status"""
        if self.auth.can(ctx.message.author, config.BOT_INFO):
            emoji = {u"\U0001F1F4" : discord.Status.online, u"\U0001F1EE" : discord.Status.idle, u"\U0001F1E9" : discord.Status.dnd}
            choice = await Utils.emoji_vote(self.client, emoji, ctx.message)
            if choice: # choice is None if it recieved no reaction
                await self.client.change_presence(status = choice)
                print("Status successfully changed")

    @commands.command(pass_context=True,
                  description="Change the bot username",
                  brief="Username",
                  help="... modifies bot informations : username")
    async def setUsername(self, ctx, url=None):
        """Change the bot username. Limited to twice per hour by discord."""
        if self.auth.can(ctx.message.author, config.BOT_INFO):
            name = Utils.parse_message_content(ctx)["message"]
            await self.client.edit_profile(username=name)
            print("Username successfully changed")

    @commands.command(pass_context=True,
                      description="Change the bot avatar",
                      brief="Avatar",
                      help="... modifies bot informations : avatar")
    async def setAvatar(self, ctx, url=None):
        """Change the bot avatar. Limited by discord ?"""
        if self.auth.can(ctx.message.author, config.BOT_INFO):
            if ctx.message.attachments: # Multiple links, we choose first, fuck it
                url = ctx.message.attachments[0]['url']
            else: # Only one
                url = url.strip('<>')

            with aiohttp.Timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        await self.client.edit_profile(avatar=await resp.read())
            print("Profile picture successfully changed")

def setup(client):
    client.add_cog(General(client, db.cursor, db.auth))
