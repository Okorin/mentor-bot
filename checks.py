import database_connection as db
import config


def all_action(ctx):
    return db.auth.can(ctx.message.author, config.ALL_ACTION_ID)


def run_commands(ctx):
    return db.auth.can(ctx.message.author, config.RUN_COMMANDS_ID)


def verify_users(ctx):
    return db.auth.can(ctx.message.author, config.VERIFY_USERS)


def debug(ctx):
    return db.auth.can(ctx.message.author, config.DEBUG)


def delete_users(ctx):
    return db.auth.can(ctx.message.author, config.DELETE_USERS)


def create_cycles(ctx):
    return db.auth.can(ctx.message.author, config.CREATE_CYCLES)


def rename_cycles(ctx):
    return db.auth.can(ctx.message.author, config.RENAME_CYCLES)


def reschedule_cycles(ctx):
    return db.auth.can(ctx.message.author, config.RESCHEDULE_CYCLES)


def add_participants(ctx):
    return db.auth.can(ctx.message.author, config.ADD_PARTICIPANTS)


def associate_participants(ctx):
    return db.auth.can(ctx.message.author, config.ASSOCIATE_PARTICIPANTS)


def blacklist_channels(ctx):
    return db.auth.can(ctx.message.author, config.BLACKLIST_CHANNELS)