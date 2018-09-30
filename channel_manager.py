import database_connection as db
from discord.ext import commands
import checks
import config


class ChannelManager:

    def __init__(self, cursor, client):
        self.client = client
        self.cursor = cursor
        self.channels = dict()
        self._preload_channels()

    def _preload_channels(self):
        query = 'SELECT channel_id, channel_type ' \
                'FROM channel_labels '
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        for result in results:
            if self.channels.get(result[1]) is None:
                self.channels[result[1]] = list()
                self.channels[result[1]].append(result[0])
            else:
                self.channels[result[1]].append(result[0])

    def is_type(self, channel, channel_type):
        search = self.channels.get(channel_type)
        if search and channel in search:
            return True
        return False

    @commands.group(pass_context=True)
    async def channel(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid subcommand')

    @channel.command()
    async def refresh(self):
        self.channels = dict()
        self._preload_channels()
        await self.client.say('Reloaded')

    @channel.command(pass_context=True)
    @commands.check(checks.blacklist_channels)
    async def blacklist(self, ctx):
        for channel in ctx.message.channel_mentions:
            await self.insert_channel(channel,
                                      config.CHANNEL_TYPES["BLACKLISTED"],
                                      ctx.message.channel,
                                      'Channel {} is already blacklisted'.format(channel.mention),
                                      'Channel {} successfully blacklisted'.format(channel.mention))

    @channel.command(pass_context=True)
    @commands.check(checks.blacklist_channels)
    async def unlist(self, ctx,):
        pass

    async def insert_channel(self, channel, channel_type, feedback_channel=None, on_error_msg='', on_success_msg=''):
        channels = self.channels.get(channel_type)

        if channels is not None and channel.id in channels:
            if feedback_channel:
                await self.client.send_message(feedback_channel, on_error_msg)
        else:
            query = 'INSERT INTO channel_labels (channel_id, channel_type) ' \
                    'VALUES (\'{}\', \'{}\')'.format(channel.id, channel_type)
            self.cursor.execute(query)
            if self.cursor.rowcount != 0:
                if feedback_channel:
                    await self.client.send_message(feedback_channel, on_success_msg)
            else:
                if feedback_channel:
                    await self.client.send_message(feedback_channel, 'Insert failed...')



def setup(client):
    client.add_cog(ChannelManager(db.cursor, client))