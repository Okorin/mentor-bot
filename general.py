from discord.ext import commands
import database_connection as db
from io import BytesIO
import aiohttp
import config


class General:

    def __init__(self, client, cursor, auth):
        self.client = client
        self.cursor = cursor
        self.auth = auth

    @commands.command(description="Says 'Pong!'",
                      brief="Says 'Pong!'",
                      help="... provided the bot is alive")
    async def ping(self):
        await self.client.say('Pong!')

    @commands.command(pass_context=True,
                      help="uses the inspirobot api, for more information, look into "
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


def setup(client):
    client.add_cog(General(client, db.cursor, db.auth))