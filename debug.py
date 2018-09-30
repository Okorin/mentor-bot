import discord
from discord.ext import commands
import database_connection as db
import config
import formatters
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client import file, client, tools
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
import checks


class Debug:

    def __init__(self, client, cursor, auth):
        self.client = client
        self.cursor = cursor
        self.auth = auth

    @commands.command(pass_context=True,
                      description="Queries Role Information",
                      brief="Queries Role Information",
                      help="searches the server for roles matching the pattern")
    @commands.check(checks.debug)
    async def getRoleIds(self, ctx, *args):
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

    @commands.command(pass_context=True)
    @commands.check(checks.debug)
    async def test(self, ctx):
        query = 'SELECT id, name, osu_user_id, verified, discord_id ' \
                'FROM users ' \
                'WHERE deleted_at IS NULL'
        self.cursor.execute(query)
        headings = ['ID', 'Username', 'osu! user ID', 'verified', 'Discord ID']
        lines = self.cursor.fetchall()
        output = formatters.CSVFormatter(headings, lines).get_output()

        await self.client.send_file(ctx.message.channel, fp=output["stream"], filename=output["name"])
        output["stream"].close()

    @commands.command()
    @commands.check(checks.debug)
    async def test_gspread(self):
            query = 'SELECT id, name, osu_user_id, verified, discord_id ' \
                    'FROM users ' \
                    'WHERE deleted_at IS NULL'
            self.cursor.execute(query)
            headings = ['DB id', 'Username', 'osu! user id', 'verified', 'Discord id']
            lines = self.cursor.fetchall()
            formatter = formatters.GoogleSheetsFormatter(headings, lines)
            sheet_url = formatter.get_output()
            await self.client.say(sheet_url)

    @commands.command()
    @commands.check(checks.debug)
    async def test_calendar(self):
        service = build(config.GOOGLE_CAL_API["BUILD_ID"],
                        config.GOOGLE_CAL_API["BUILD_VERSION"],
                        credentials=ServiceAccountCredentials.from_json_keyfile_name(config.CREDENTIALS_FILE,
                                                                                     config.GOOGLE_CAL_API["SCOPES"]))

        now = datetime.datetime.utcnow().isoformat() + 'Z'

        events_result = service.events().list(calendarId=config.GOOGLE_CAL_API["CALENDAR_ID"],
                                              maxResults=10, singleEvents=True, timeMin=now,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])


def setup(client):
    client.add_cog(Debug(client, db.cursor, db.auth))