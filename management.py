import discord
from discord.ext import commands
import database_connection as db
import config
import html
import ibm_db_dbi
import aiohttp
import datetime
import json
import asyncio
import checks


def now():
    return '\'{}\''.format(str(datetime.datetime.utcnow()))


def to_str(datetime):
    return '\'{}\''.format(str(datetime))


class Management:

    def __init__(self, client, cursor):
        self.client = client
        self.cursor = cursor
        self.gamemodes = self._preload_value_list('gamemodes')
        self.cycle_user_types = self._preload_value_list('cycle_users_types')

    def _preload_value_list(self, table_name):
        query = 'SELECT id, name FROM {}'.format(table_name)
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        if result:
            return {result[i][1]: result[i][0] for i in range(0, len(result))}
        return dict()

    async def _parse_datetime(self, ctx, date_string, return_as_string=True):
        dt = None
        try:
            dt = datetime.datetime.strptime(date_string, '%d.%m.%Y')
            if return_as_string:
                return '\'{}\''.format(str(dt))
            else:
                return dt
        except ValueError:
            await self.client.send_message(ctx.message.channel,
                                           'Formatting of {} into a proper timestamp failed'.format(date_string))
        return dt

    def _get_member_from_db(self, member):
        if isinstance(member, discord.Member):
            query = 'SELECT name, osu_user_id, discord_id, verified, id ' \
                    'FROM users WHERE discord_id = \'{}\' and deleted_at IS NULL'.format(member.id)
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result
        return None

    # The cycle users Resource
    @commands.group(pass_context=True,
                    help="Manage the cycle resource",
                    description="Grants access to the cycle resource")
    async def participant(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid subcommand')

    @participant.command(pass_context=True,
                         help="",
                         description="")
    @commands.check(checks.add_participants)
    async def add(self, ctx, name, cycle: int, gamemode, user_type):
        # load mode from customizing
        mode_id = self.gamemodes.get(gamemode)

        # load usertype from cuztomizing
        user_type_id = self.cycle_user_types.get(user_type)

        # one of the keys could not be found
        if not mode_id or not user_type_id:
            await self.client.say('Invalid customizing, check cycle_users_types and gamemodes')
        else:
            # grab the member
            member = discord.utils.find(lambda m: name == m.name or name == m.nick, ctx.message.server.members)
            if not member:
                await self.client.say('{} not found!'.format(name))
            else:
                # check whether or not the cycle actually exists
                query = 'SELECT id FROM cycles WHERE id = {}'.format(cycle)
                self.cursor.execute(query)

                # yes
                if self.cursor.fetchone():
                    user = self._get_member_from_db(member)
                    if user:
                        # final check: does this combination already exist as a cycle user
                        query = 'SELECT id FROM cycle_users WHERE ' \
                                'cycles_id = {cycle} and ' \
                                'users_id = {user} and ' \
                                'gamemodes_id = {gamemode} and ' \
                                'types_id = {user_type}'.format(cycle=cycle,
                                                                user=user[4],
                                                                gamemode=mode_id,
                                                                user_type=user_type_id)
                        self.cursor.execute(query)
                        if not self.cursor.fetchone():
                            # attempt inserting
                            query = 'INSERT INTO cycle_users ' \
                                    '(cycles_id, users_id, gamemodes_id, types_id) ' \
                                    'VALUES ({},{},{},{})'.format(cycle,user[4],mode_id,user_type_id)
                            print(query)
                            self.cursor.execute(query)
                            if self.cursor.rowcount == 1:
                                # confirm this to the user
                                await self.client.say('Added {name} as a {user_type} '
                                                      'to cycle {cycle} for {gamemode}'.format(name=name,
                                                                                               user_type=user_type,
                                                                                               cycle=cycle,
                                                                                               gamemode=gamemode))
                            else:  # query failed??
                                await self.client.say('Cycle User creation failed')
                        else:  # this thing already exists
                            await self.client.say('This cycle user already exists')
                else:  # no cycle
                    await self.client.say('Cycle {} not found'.format(cycle))

    @participant.command(pass_context=True,
                         help="",
                         description="")
    @commands.check(checks.add_participants)
    async def remove(self, ctx):
        pass

    @participant.command(pass_context=True,
                         help="",
                         description="")
    @commands.check(checks.associate_participants)
    async def associate(self, ctx, name1, name2, cycle: int, gamemode):
        # load mode from customizing
        mode_id = self.gamemodes.get(gamemode)

        # nothing found
        if not mode_id:
            await self.client.say('Invalid gamemode')
        else:
            query = 'SELECT id FROM cycles WHERE id = {}'.format(cycle)
            self.cursor.execute(query)

            # found
            if not self.cursor.fetchone():
                await self.client.say('Cycle {} not found'.format(cycle))
            else:

                # get the users
                user1 = discord.utils.find(lambda m: m.name == name1 or m.nick == name1, ctx.message.server.members)
                user2 = discord.utils.find(lambda m: m.name == name2 or m.nick == name2, ctx.message.server.members)
                if not user1:
                    await self.client.say('User {} not found'.format(name1))
                if not user2:
                    await self.client.say('User {} not found'.format(name2))
                if user1 and user2:

                    # read what they are in the database
                    user_a = self._get_member_from_db(user1)
                    user_b = self._get_member_from_db(user2)

                    # both are found
                    if user_a and user_b:

                        # check whether these two users
                        # checks for equality on gamemodes, cycles and inequality on type
                        query = 'SELECT a.id, b.id ' \
                                'FROM cycle_users AS a ' \
                                'JOIN cycle_users AS b ' \
                                'ON a.cycles_id = b.cycles_id ' \
                                'AND a.types_id != b.types_id ' \
                                'AND a.gamemodes_id = b.gamemodes_id ' \
                                'WHERE a.users_id = {user1} AND b.users_id = {user2} ' \
                                'AND a.gamemodes_id = {gamemode} ' \
                                'AND a.cycles_id = {cycle}'.format(user1=user_a[4],
                                                                   user2=user_b[4],
                                                                   cycle=cycle,
                                                                   gamemode=mode_id)

                        self.cursor.execute(query)
                        result = self.cursor.fetchone()
                        if result:

                            # users are compatible so try inserting them
                            query = 'INSERT INTO user_relationships (cycle_users_id, cycle_users_id1) ' \
                                    'VALUES ({}, {})'.format(result[0], result[1])

                            # the error message is fucking useless anyways
                            try:
                                self.cursor.execute(query)
                            except ibm_db_dbi.Error:
                                await self.client.say('Insertion failed (combination already exists)')

                            # affected rows = 1 means the query went thru as is
                            if self.cursor.rowcount == 1:
                                await self.client.say('Association created')
                        else:
                            await self.client.say('Users are incompatible')

    # The cycle Resource
    @commands.group(pass_context=True,
                    help="Manage the cycle resource",
                    description="Grants access to the cycle resource")
    async def cycle(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid subcommand')

    @cycle.command(pass_context=True,
                   help="Creates a new cycle provided all parameters are set correctly. "
                        "The input parameters are parsed against the expression DD.MM.YYYY and fails if that fails. ",
                   brief="Create a new cycle",
                   description="Create a new cycle")
    @commands.check(checks.create_cycles)
    async def create(self, ctx, name, mentor_starts_at, mentor_ends_at,
                     mentee_starts_at, mentee_ends_at,
                     starts_at, ends_at):
        # escape name before inserting anything
        name = '\'{}\''.format(html.escape(name))
        created_at = now()

        # i dont remember why i made these async
        starts_at = await self._parse_datetime(ctx, starts_at, False)
        ends_at = await self._parse_datetime(ctx, ends_at, False)
        mentor_starts_at = await self._parse_datetime(ctx, mentor_starts_at, False)
        mentor_ends_at = await self._parse_datetime(ctx, mentor_ends_at, False)
        mentee_starts_at = await self._parse_datetime(ctx, mentee_starts_at, False)
        mentee_ends_at = await self._parse_datetime(ctx, mentee_ends_at, False)

        # local check function that either fails or gives you both values back
        def check(start, end):
            if start > end:
                return False
            else:
                return [to_str(start), to_str(end)]

        # check all the times lazily (aka a lot of code)
        if starts_at and ends_at:
            chk = check(starts_at, ends_at)
            if not chk:
                await self.client.say('Invalid date range provided for cycle start and end')
            else:
                starts_at = chk[0]
                ends_at = chk[1]
        else:
            chk = False

        if mentor_starts_at and mentor_ends_at and chk:
            chk = check(mentor_starts_at, mentor_ends_at)
            if not chk:
                await self.client.say('Invalid date range provided for mentor signups start and end')
            else:
                mentor_starts_at = chk[0]
                mentor_ends_at = chk[1]
        else:
            chk = False

        if mentee_starts_at and mentee_ends_at and chk:
            chk = check(mentee_starts_at, mentee_ends_at)
            if not chk:
                await self.client.say('Invalid date range provided for mentee signups start and end')
            else:
                mentee_starts_at = chk[0]
                mentee_ends_at = chk[1]
        else:
            chk = False

        # if the chk made it to here and is still not false it made it through all checks
        if chk:
            query = 'INSERT INTO cycles (name, starts_at, ends_at, mentor_starts_at, mentor_ends_at, ' \
                    'mentee_starts_at, mentee_ends_at, created_at) ' \
                    'VALUES ({}, {}, {}, {}, {}, {}, {}, {})'.format(name,
                                                                     starts_at,
                                                                     ends_at,
                                                                     mentor_starts_at,
                                                                     mentor_ends_at,
                                                                     mentee_starts_at,
                                                                     mentee_ends_at,
                                                                     created_at)

            self.cursor.execute(query)
            await self.client.say('Created {} cycle'.format(self.cursor.rowcount))

    @cycle.command(
                   help="Of course this only works if the cycle is actually found",
                   brief="Changes the name of a cycle",
                   description="Changes the name of a cycle")
    @commands.check(checks.rename_cycles)
    async def name(self, cycle_id: int, name):
        query = 'UPDATE cycles SET name = \'{name}\', ' \
                'updated_at = {now} WHERE id = {cycle_id}'.format(name=html.escape(name),
                                                                  now=now(),
                                                                  cycle_id=cycle_id)
        self.cursor.execute(query)
        if self.cursor.rowcount == 1:
            await self.client.say("Name of cycle {cid} was changed to {name}".format(name=html.escape(name),
                                                                                     cid=cycle_id))
        else:
            await self.client.say("Cycle not found")

    async def update_range(self, ctx, cycle_id: int, start, end, start_name, end_name):

        # same local checker as above
        def check(start_dt, end_dt):
            if start_dt > end_dt:
                return False
            else:
                return [to_str(start_dt), to_str(end_dt)]

        start = await self._parse_datetime(ctx, start, False)
        end = await self._parse_datetime(ctx, end, False)

        chk = False

        if start and end:
            chk = check(start, end)
            if not chk:
                await self.client.say('Invalid date range')
            else:
                start = chk[0]
                end = chk[1]

        if chk:
            query = 'UPDATE cycles SET {sname} = {start}, {ename} = {end}, ' \
                    'updated_at = {now} WHERE id = {cycle_id}'.format(start=start,
                                                                      end=end,
                                                                      sname=start_name,
                                                                      ename=end_name,
                                                                      now=now(),
                                                                      cycle_id=cycle_id)
            self.cursor.execute(query)
            if self.cursor.rowcount == 1:
                await self.client.say("Cycle {cid} timeslot changed".format(cid=cycle_id))
            else:
                await self.client.say("Cycle not found")

    @cycle.command(pass_context=True,
                   help="Of course this only works if the cycle is actually found",
                   brief="Changes the mentor signup period of a cycle",
                   description="Changes the mentor signup period of a cycle")
    @commands.check(checks.reschedule_cycles)
    async def mentorSignups(self, ctx, cycle_id: int, start, end):
        await self.update_range(ctx, cycle_id, start, end, 'mentor_starts_at', 'mentor_ends_at')

    @cycle.command(pass_context=True,
                   help="Of course this only works if the cycle is actually found",
                   brief="Changes the mentee signup period of a cycle",
                   description="Changes the mentee signup period of a cycle")
    @commands.check(checks.reschedule_cycles)
    async def menteeSignups(self, ctx, cycle_id: int, start, end):
        await self.update_range(ctx, cycle_id, start, end, 'mentee_starts_at', 'mentee_ends_at')

    @cycle.command(pass_context=True,
                   help="Of course this only works if the cycle is actually found",
                   brief="Changes the duration of a cycle",
                   description="Changes the duration of a cycle")
    @commands.check(checks.reschedule_cycles)
    async def duration(self, ctx, cycle_id: int, start, end):
        await self.update_range(ctx, cycle_id, start, end, 'starts_at', 'ends_at')

    @cycle.command(help="Selects the metadata about the relevant cycle",
                   brief="displays cycle information",
                   description="displays cycle information")
    async def get(self, cycle_id: int):
        query = 'SELECT name, mentor_starts_at, mentor_ends_at, ' \
                'mentee_starts_at, mentee_ends_at, ' \
                'starts_at, ends_at ' \
                'FROM cycles ' \
                'WHERE id = {cycle_id}'.format(cycle_id=cycle_id)
        self.cursor.execute(query)

        # since this thing is an index operation we can only get 1 result anyways
        result = self.cursor.fetchone()
        if not result:
            await self.client.say('Cycle not found')
        else:
            embed = discord.Embed(title='Query Results', colour=discord.Colour.blue())
            embed.add_field(name="Name", value=result[0], inline=False)
            embed.add_field(name="Mentor Signups", value='{start} - {end}'.format(start=result[1],
                                                                                  end=result[2]),
                            inline=False)
            embed.add_field(name="Mentee Signups", value='{start} - {end}'.format(start=result[3],
                                                                                  end=result[4]),
                            inline=False)
            embed.add_field(name="Duration", value='{start} - {end}'.format(start=result[5],
                                                                            end=result[6]),
                            inline=False)
            await self.client.say(embed=embed)

    @cycle.command(help="Gets the users of a Cycle")
    async def users(self, cycle: int):
        query = 'SELECT cyc.users_id, cyc.gamemodes_id, cyc.types_id, ' \
                'us.discord_id, us.name, gamemodes.name, cycle_users_types.name ' \
                'FROM cycle_users as cyc ' \
                'JOIN users as us ' \
                'on cyc.users_id = us.id ' \
                'JOIN gamemodes ' \
                'on gamemodes.id = cyc.gamemodes_id ' \
                'join cycle_users_types ' \
                'on cycle_users_types.id = cyc.types_id ' \
                'where cyc.cycles_id = {}'.format(cycle)
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        if not results:
            await self.client.say('No users found!')
        else:
            output = dict()
            output["Mentors"] = str()
            output["Mentees"] = str()
            print(results)
            for result in results:
                if result[2] == self.cycle_user_types.get('Mentor'):
                    output["Mentors"] += result[4] + ' '
                elif result[2] == self.cycle_user_types.get('Mentee'):
                    output["Mentees"] += result[4] + ' '

            if not output['Mentors']:
                output['Mentors'] = 'No Users'
            if not output['Mentees']:
                output['Mentees'] = 'No Users'

            await self.client.say('Mentors: ' + output['Mentors'])
            await self.client.say('Mentees: ' + output['Mentees'])


    @cycle.command(help="Multiple cycles can be considered to be 'active' during mentor signups",
                   brief="Gets the active cycle(s)",
                   description="Gets the active cycle(s)")
    async def active(self):
        query = 'SELECT id, name FROM cycles WHERE ' \
                '( starts_at <= {now} and ends_at >= {now}) OR ' \
                '( mentor_starts_at <= {now} and mentor_ends_at >= {now}) OR ' \
                '( mentee_starts_at <= {now} and mentee_ends_at >= {now})'.format(now=now())
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        if results:
            embed = discord.Embed(title='Active Cycles', color=discord.Colour.blue())
            for result in results:
                embed.add_field(name=result[1], value='id: {}'.format(result[0]))
            await self.client.say(embed=embed)

    @cycle.command(help="gets the running cycle(s) - technically this query can return multiple lines",
                   brief="Gets the running cycle(s)",
                   description="Gets the running cycle(s)")
    async def running(self):
        query = 'SELECT id, name FROM cycles WHERE ' \
                '( starts_at <= {now} and ends_at >= {now})'.format(now=now())
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        if results:
            embed = discord.Embed(title='Running Cycles', color=discord.Colour.blue())
            for result in results:
                embed.add_field(name=result[1], value='id: {}'.format(result[0]))
            await self.client.say(embed=embed)

    # The user resource
    @commands.group(pass_context=True,
                    help="Manage the user resource",
                    description="Grants access to the user resource")
    async def user(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid subcommand')

    @user.command(pass_context=True,
                  description="Verifies a list of users",
                  brief="Verifies a list of users",
                  help="Users are looked up in the server the command is posted up by name "
                       "and then are searched in the database. If the user is found, "
                       "the osu!api is used to verify them")
    @commands.check(checks.verify_users)
    async def verify(self, ctx, *names):
        for name in names:
            member = discord.utils.find(lambda m: m.name == name or m.nick == name, ctx.message.server.members)
            if not member:
                await self.client.say("No member matching {}".format(name))
            else:
                results = self._get_member_from_db(member)

                if results:
                    if results[3] == 1:
                        if results[1]:
                            await self.client.send_message(ctx.message.channel,
                                                           '{} was already verified '
                                                           'as user id {}'.format(results[0],
                                                                                  results[1]))
                        else:
                            await self.client.say('{} not found.'.format(results[0]))
                    else:
                        # call the osu! api
                        if results[1] is not None:
                            username = results[1]
                        else:
                            username = results[0]

                        uri = 'https://osu.ppy.sh/api/get_user?k={key}&u={name}'.format(key=config.OSU_API_KEY,
                                                                                        name=username)
                        async with aiohttp.ClientSession() as session:
                            async with session.get(uri) as resp:
                                data = json.loads(await resp.text())
                                if data:
                                    query = 'UPDATE users ' \
                                            'SET name = \'{name}\', osu_user_id = {osu_id}, verified = 1 ' \
                                            'WHERE id = {id}'.format(name=data[0]['username'],
                                                                     osu_id=data[0]['user_id'],
                                                                     id=results[4])
                                    self.cursor.execute(query)
                                    await self.client.send_message(ctx.message.channel,
                                                                   'Linked {} to osu user id {}'.format(data[0]['username'],
                                                                                                        data[0]['user_id']))
                                await asyncio.sleep(1)

                else:
                    await self.client.send_message(ctx.message.channel, 'User {} is not in database!'.format(name))

    @user.command(pass_context=True,
                  description="Ignores the sync Status of a given member",
                  brief="Ignores the sync status of a given member",
                  help="This command sets the given members to be already verified")
    @commands.check(checks.verify_users)
    async def ignore(self, ctx, *members):
        for name in members:
            member = discord.utils.find(lambda m: m.name == html.escape(name), ctx.message.server.members)
            if not member:
                await self.client.say("No members matching {}".format(name))
            else:
                result = self._get_member_from_db(member)
                if not result:
                    await self.client.say('User {} is not in database!'.format(name))
                else:
                    query = 'UPDATE users SET verified = 1, osu_user_id = NULL WHERE id = {}'.format(result[4])
                    print(query)
                    self.cursor.execute(query)
                    await self.client.say('Updated the verified status of {}'.format(name))

    @user.command(pass_context=True,
                  description="Resets the verified status of a given member",
                  brief="Resets the verified status of a given member",
                  help="This command sets the given members to be not verified, if they weren't already")
    @commands.check(checks.verify_users)
    async def unverify(self, ctx, *members):
        for name in members:
            member = discord.utils.find(lambda m: m.name == html.escape(name), ctx.message.server.members)
            if not member:
                await self.client.say("No members matching {}".format(name))
            else:
                result = self._get_member_from_db(member)
                if not result:
                    await self.client.say('User {} is not in database!'.format(name))
                else:
                    query = 'UPDATE users SET verified = NULL,' \
                            ' updated_at = {upd}  WHERE id = {id}'.format(id=result[4],
                                                                          upd=now())
                    self.cursor.execute(query)
                    await self.client.say('Updated the verified status of {}'.format(name))

    @user.command(pass_context=True,
                  description="Prints unverified members from the database",
                  brief="Prints unverified members from the database",
                  help="This command does not take any arguments, it's a static query")
    @commands.check(checks.verify_users)
    async def unverified(self, ctx):
        query = 'SELECT name FROM users WHERE verified IS NULL and deleted_at IS NULL'
        db.cursor.execute(query)
        output = str()
        for res in db.cursor.fetchall():
            if (len(output) + len(res[0]) + 6) >= 2000:
                await self.client.send_message(ctx.message.channel, '```{}```'.format(output))
                output = str()
            if " " in res[0]:
                res[0] = '\"{}\"'.format(res[0])
            output += res[0] + ' '
        if output:
            await self.client.send_message(ctx.message.channel, '```{}```'.format(output))

    @user.command(pass_context=True,
                  description="Force deletes a user",
                  brief="Force deletes a user",
                  help="Awaits confirmation before doing so, soft deletes the user in case confirmation is provided")
    @commands.check(checks.delete_users)
    async def delete(self, ctx, *names):
        def check(msg):
            return msg.content.startswith('y') or msg.content.startswith('n')
        for name in names:
            query = 'SELECT id FROM users WHERE name =\'{}\''.format(html.escape(name))
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            if result:
                await self.client.say("Confirm deleting user {} (y/n)".format(name))
                msg = await self.client.wait_for_message(timeout=10, author=ctx.message.author, check=check)
                if msg:
                    if msg.content.startswith('y'):
                        query = 'UPDATE users SET updated_at = {now}, ' \
                                'deleted_at = {now} WHERE id = {id}'.format(now=now(), id=result[0])
                        self.cursor.execute(query)
                        await self.client.say('Deleted user {}'.format(name))
                    else:
                        await self.client.say("Action aborted")
                        break


def setup(client):
    client.add_cog(Management(client, db.cursor))