import ibm_db
import ibm_db_dbi
import config
import pprint
p = pprint.PrettyPrinter(indent=4)

ibm_conn = ibm_db.pconnect('DATABASE={dbna};HOSTNAME={host};PORT={port};PROTOCOL={prot};UID={user};PWD={pasw}'
                           .format(dbna=config.DATABASE,
                                   host=config.HOSTNAME,
                                   port=config.PORTNUMB,
                                   prot=config.PROTOCOL,
                                   user=config.USERNAME,
                                   pasw=config.PASSWORD), '', '')
conn = ibm_db_dbi.Connection(ibm_conn)
cursor = conn.cursor()


# Command authority Checker (can be used inside of commands)
class AuthorityCheck:

    def __init__(self, connection, bot_roles_table='bot_roles', actions='actions',
                 permissions='permissions', guild_roles='guild_roles'):
        # Database connection
        self.conn = connection
        self.cursor = connection.cursor()

        # name of the bot roles table
        self.roles = bot_roles_table

        # name of the actions table (basically an ACL List on a server)
        self.actions = actions

        # permissions are a combination of actions and bot roles
        self.permissions = permissions

        # guild roles assign bot roles to roles in a discord guild
        self.guild_roles = guild_roles

        # the roles roles list is ~cached~ or whatever this is to minimize the actual times we have to retrieve them
        # from the database
        # this list currently only refreshes on restart
        self.cache = list()

    def has(self, member, action):
        """
        This method does a simple authority check by either reading its cache or retrieving the data from the database
        :param member: a guild Member Object
        :param action: the action to check against
        :return:
        """
        # roles of the member
        roles = member.roles

        # server of the member
        server = member.server

        # search in cache for whether or not this server ID was already queried
        results = [c for c in self.cache if c[0] == server.id]

        # results is still empty
        if not results:
            query = 'SELECT {gr}.role_id, {gr}.bot_roles_id, {pr}.actions_id ' \
                    'FROM {gr} ' \
                    'JOIN {pr} on {pr}.bot_roles_id = {gr}.bot_roles_id ' \
                    'WHERE {gr}.guild_id = \'{serverId}\''.format(serverId=server.id,
                                                                  gr=self.guild_roles,
                                                                  pr=self.permissions)
            # execute this query
            self.cursor.execute(query)

            # fetch all results
            results = self.cursor.fetchall()

            # append all results to ~cache~
            self.cache.append([server.id, results])
        else:
            # since the result itself is a tuple inside a list this is the way this result is accessed again
            results = results[0][1]

        # go through the results
        for result in results:

            # actually check if the combination of action and role is somewhere in the set of results
            matches = [role for role in roles if role.id == result[0] and result[2] == action]

            # a match means the user is in a role that owns the asked for permissions
            if matches:
                return True

        # if the program got here, the asked permission was in no role for the user
        return False

    # wraps global authority check up to run always instead of requiring checking it separately
    # (and subsequently forgetting it)
    def can(self, member, action):
        return True
        # if another action is requested
        if action != config.ALL_ACTION_ID:

            # the all action logically overwrites all other actions
            return self.has(member, action) or self.has(member, config.ALL_ACTION_ID)

        # if it is the all action id only do one check
        return self.has(member, config.ALL_ACTION_ID)


auth = AuthorityCheck(conn)
