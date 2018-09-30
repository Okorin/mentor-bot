import database_connection as db
import discord.ext.commands as commands
import discord
import config
import datetime
import asyncio
import random
import html
from ratelimits import RateLimit


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
extensions = ['general', 'management', 'debug', 'channel_manager']
shitpost_rate = RateLimit(config.SHITPOST_RATE_LIMIT["rate"], config.SHITPOST_RATE_LIMIT["per"])


async def sync_users():
    await client.wait_until_ready()
    while not client.is_closed:
        print('Scanning for new users')
        query = 'SELECT discord_id FROM users WHERE discord_id in ('

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
        if message.author.bot:
            return
        manager = client.get_cog("ChannelManager")
        if manager and manager.is_type(message.channel.id, config.CHANNEL_TYPES["BLACKLISTED"]):
            print("channel blacklisted!")
            return
        await shitpost(message)
        if auth.can(message.author, config.RUN_COMMANDS_ID):
            await client.process_commands(message)


async def shitpost(message):
    # determine a new random number (apparently not assigning it to something causes different behaviour)
    randint = random.randrange(1, config.TRIGGER_LIKELIHOOD + 1)

    # determine if the random number is the limit
    # or one of the trigger phrases is in the message
    # AND the author must not be a bot to avoid playing ping pong with other bots
    if (randint == config.TRIGGER_LIKELIHOOD
            or [phrase for phrase in config.TRIGGER_PHRASES if phrase in message.content.lower()]) \
            and not message.author.bot:
        await guaranteed_shitpost(message, 5)


async def guaranteed_shitpost(message, limit):
    # get a random date from the created at date of the channel to now
    randdat = random_date(message.channel.created_at, datetime.datetime.utcnow())

    # read limit amount of log messages (getting one random message is forbidden by the framework)
    # it tells you to use get message instead but that assumes you know the message's id...
    generator = client.logs_from(message.channel, limit=limit,
                                 around=randdat)

    # determine which message to output
    message_to_output = random.randint(1, limit + 1)
    counter = 1

    # go through the messages in the generator
    async for msg in generator:

        # the message needs to have content, im sure af not going to copy all attachments etc...
        if msg.content and message_to_output == counter:

            # the message must not contain any mentions that the bot could just randomly do
            if not msg.mentions and not msg.role_mentions and not msg.mention_everyone:

                # determine if the action is being rate limited?
                secs_til_next = shitpost_rate.is_rate_limited()

                if not secs_til_next:  # do it
                    await client.send_message(message.channel, msg.content)
                else:  # print out when to do it.
                    print('Next attempt can be made in {} seconds'.format(secs_til_next))
                    break
            else:
                message_to_output += 1
        counter += 1


def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)


if __name__ == '__main__':
    for extension in extensions:
        try:
            print('attempting to load extension {}'.format(extension))
            client.load_extension(extension)
        except Exception as error:
            print('{} cannot be loaded. [{}]'.format(extension, error))
    client.loop.create_task(sync_users())
    client.run(config.SECRET)
