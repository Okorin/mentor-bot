import discord
from discord.ext import commands
import database_connection as db
import config

class Debug:

    def __init__(self, client, cursor, auth):
        self.client = client
        self.cursor = cursor
        self.auth = auth

    @commands.command(pass_context=True,
                      description="Queries Role Information",
                      brief="Queries Role Information",
                      help="searches the server for roles matching the pattern")
    async def getRoleIds(self, ctx, *args):
        if self.auth.can(ctx.message.author, config.DEBUG):
            embed = discord.Embed(title='Query Results', colour=discord.Colour.gold())
            for arg in args:
                roles = [role for role in ctx.message.server.roles if arg in role.name]
                if roles:
                    for role in roles:
                        embed.add_field(name=role.name, value=role.id)

            await self.client.say(embed=embed)

    @commands.command(pass_context=True,
                      description="Refreshes permission cache",
                      help="Refreshes permission cache")
    async def refreshAuthCache(self, ctx):
        if self.auth.can(ctx.message.author, config.DEBUG):
            self.auth.refresh()
            await self.client.say('Reset auth cache, the subsequent operations will be read from DB')


def setup(client):
    client.add_cog(Debug(client, db.cursor, db.auth))