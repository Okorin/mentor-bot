import config
import asyncio
import discord
from discord.ext import commands
#from discord.utils import get 

class Utils:
    """Utils class : used for common actions in the bot functions."""
    def parse_message_content(ctx):
        """Returns a dict of arguments."""
        command, *args = ctx.message.content.split()
        command = command[len(config.COMMAND_PREFIX):].lower().strip() # I have the command too, maybe one day it will be useful ?
        #Here we get all the data related to a message. Maybe it's too much ?
        data = dict()
        data['message'] = " ".join(args) # is just the message without the command
        data['cmd_args'] = args # is a list of parsed arguments
        data['channel'] = ctx.message.channel
        data['author'] = ctx.message.author
        data['server'] = ctx.message.server
        data['user_mentions'] = list(map(ctx.message.server.get_member, ctx.message.raw_mentions))
        data['channel_mentions'] = list(map(ctx.message.server.get_channel, ctx.message.raw_channel_mentions))
        return data

    def paginate(content, *, length=config.DISCORD_MAX_LENGTH, reserve=0):
        """Splits 2k+ messages into multiples messages for discord to handle it."""
        if type(content) == str: # Let's just check if we have a correct input, just in case
            contentlist = content.split('\n')
        elif type(content) == list:
            contentlist = content
        else:
            raise ValueError("Content must be str or list, not %s" % type(content))

        chunks = []
        currentchunk = ''

        for line in contentlist:
            if len(currentchunk) + len(line) < length - reserve:
                currentchunk += line + '\n'
            else:
                chunks.append(currentchunk)
                currentchunk = ''

        if currentchunk: # If the string has at least one char, otherwise it's useless
            chunks.append(currentchunk)

        return chunks

    def write_file(filename, contents): # Made that just in case one day we need to write a file to send it xd
        """Writes a file in UTF-8 to keep all the info."""
        with open(filename, 'w', encoding='utf8') as f:
            for item in contents:
                f.write(str(item))
                f.write('\n')
            f.close()

    async def emoji_vote(self, emojiData, message, timeout=60):
        """Takes a list or dict of emojis (unicode form (goto https://www.iemoji.com/), a message object
        and awaits for a correct reaction to continue. Will dismiss the request in 60 seconds by default."""
        #print(get(message.server.emojis, name="emoji_name")) Custom emoji object if needed someday
        emojiList = list()
        if type(emojiData) == dict: # if it's a dict : it will have items to convert at the end, convert it into a list to continue
            for key in emojiData.keys():
                emojiList.append(key)
        elif type(emojiData) == list: # just copy the list
            emojiList = list(emojiData)
        else:
            raise ValueError("Content must be dict or list, not %s" % type(emojiData))

        for emoji in emojiList:
            await self.add_reaction(message, emoji)
        trigger = await self.wait_for_reaction(emojiList, message=message, user=message.author, timeout=timeout)
        if trigger != None: # If None then the user didn't responded
            for emoji in emojiList:
                if str('{0.reaction.emoji}'.format(trigger)) == emoji:
                    if type(emojiData) == dict: # if it's a dict : we convert it into the corresponding item
                        return emojiData[emoji]
                    else:
                        return emoji
        return None
