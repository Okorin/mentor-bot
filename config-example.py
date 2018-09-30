# Database connection data
DATABASE = 'BLUDB'
HOSTNAME = ''
PORTNUMB = '50001'
USERNAME = ''
PROTOCOL = 'TCPIP'
PASSWORD = ''

# Discord bot token
SECRET = ''
COMMAND_PREFIX = '~'
OSU_API_KEY = ''

# General
DISCORD_MAX_LENGTH = 2000

# Spreadsheets Creds File
CREDENTIALS_FILE = 'credentials.json'
SERVICE_ACCOUNT_SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
ADMIN_MAIL_ADDRESS = ''

# Google Calendar API
GOOGLE_CAL_API = dict()
GOOGLE_CAL_API["BUILD_ID"] = 'calendar'
GOOGLE_CAL_API["BUILD_VERSION"] = 'v3'
GOOGLE_CAL_API["SCOPES"] = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CAL_API["CALENDAR_ID"] = 'penilji04k7p6nf5sjh26mio1o@group.calendar.google.com'

# Command authorization keys
ALL_ACTION_ID = 1
RUN_COMMANDS_ID = 2
VERIFY_USERS = 3
DEBUG = 21
DELETE_USERS = 22
CREATE_CYCLES = 23
RENAME_CYCLES = 24
RESCHEDULE_CYCLES = 25
ADD_PARTICIPANTS = 26
ASSOCIATE_PARTICIPANTS = 27
BLACKLIST_CHANNELS = 28
ADMINISTRATE_BOT = 29

# channeltypes
CHANNEL_TYPES = dict()
CHANNEL_TYPES["BLACKLISTED"] = "BLACKLISTED"
CHANNEL_TYPES["ANNOUNCE"] = "ANNOUNCE"

# rate limits:
SHITPOST_RATE_LIMIT = dict()
SHITPOST_RATE_LIMIT["rate"] = 5
SHITPOST_RATE_LIMIT["per"] = 60

# Likelyhood of random messages triggering the shitposting mechanism
TRIGGER_LIKELIHOOD = 200
TRIGGER_PHRASES = ['kyou']
