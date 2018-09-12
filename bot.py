import database_connection as db
import discord.ext.commands as commands
#from discord import utils
import discord
import config
import datetime
import asyncio
from io import BytesIO
import html
import aiohttp
import json


class GuildUser:
    def __init__(self, name, discord_id, creat):
        self.name = name
        self.discord_id = discord_id
        self.creat = creat

    def __eq__(self, other):
        return self.discord_id == other.discord_id

    def __ne__(self, other):
        return self.discord_id != other.discord_id

    def __hash__(self):
        return hash(self.discord_id)

    def __lt__(self, other):
        return int(self.discord_id[:10]) < int(other.discord_id[:10])


# discord client
client = commands.Bot(command_prefix=config.COMMAND_PREFIX)
auth = db.auth
extensions = ['general', 'management', 'debug']


async def sync_users():
    await client.wait_until_ready()
    while not client.is_closed:
        print('Scanning for new users')
        query = 'SELECT discord_id FROM uses WHERE discord_id in ('

        # needs two of these because there's no simple way of cloning a generator and getting all members returns one
        members = client.get_all_members()
        members2 = client.get_all_members()

        # format query (the userids dont need escaping)
        for member in members:
            query += '\'{}\','.format(member.id)
        query = query[:-1] + ')'
        db.cursor.execute(query)
        results = db.cursor.fetchall()

        # init set (used to avoid duplicate inserts [disclaimer: hopefully])
        uids = set()
        now = datetime.datetime.utcnow()
        query = 'INSERT INTO users (name, discord_id, created_at) VALUES '
        triggered_once = False
        # run through the second iterator and filter the results for the member's id
        for member in members2:
            matches = [res for res in results if member.id == res[0]]
            if not matches:
                triggered_once = True
                # haha i should write a unit test for inserting guild users into a set but who the fuck would do that
                if member.nick is not None:
                    uids.add(GuildUser(html.escape(member.nick), member.id, now))
                else:
                    uids.add(GuildUser(html.escape(member.name), member.id, now))
        for uid in uids:
            query += '(\'' + uid.name + '\',\'' + uid.discord_id + '\',\'' + str(uid.creat) + '\'),'

        if triggered_once:
            db.cursor.execute(query[:-1])
        else:
            print('nothing new to add!')

        # async sleep for 3 hours
        await asyncio.sleep(9800)

@client.event
async def on_ready():
    print('Bot started')
    print('Current Connection: {}'.format(db.ibm_db.active(db.ibm_conn)))


@client.event
async def on_message(message):
    if isinstance(message.author, discord.Member):
        if auth.can(message.author, config.RUN_COMMANDS_ID):
            await client.process_commands(message)


if __name__ == '__main__':
    for extension in extensions:
        try:
            print('attempting to load extension {}'.format(extension))
            client.load_extension(extension)
        except Exception as error:
            print('{} cannot be loaded. [{}]'.format(extension, error))
    client.loop.create_task(sync_users())
    client.run(config.SECRET)
