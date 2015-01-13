# Millionaire Makers Drawing Platform
# https://www.reddit.com/r/millionairemakers
#
# Configuration file
#
# Contact /u/minlite for comments/suggestions

# Basic auth credentials used for logging in to the drawing backend
BASIC_AUTH_USERNAME = ''
BASIC_AUTH_PASSWORD = ''

# Reddit application credentials used for oAuth
REDDIT_CLIENT_ID = ''
REDDIT_CLIENT_SECRET = ''
REDDIT_REDIRECT_URI = 'http://127.0.0.1:65010/authorize_callback'

# User agent value submitted to Reddit
# Should be unique for each client
REDDIT_USER_AGENT = 'MillionaireMakers Drawing Service v1. \n See /r/millionairemakers \n Contact /u/minlite for concerns.'

# Delay between each request to Reddit
REDDIT_API_REQUEST_DELAY = 1.0

# Dropbox application credentials used for uploading files
DROPBOX_ACCESS_TOKEN = ''

# When enabled, limits moderation to one user
LIMIT_MODERATION = False
# Username allowed to moderate drawings (used with LIMIT_MODERATION set to True)
MODERATOR_USERNAME = ''

# Winner block
# Each block ~ 10 minutes
WINNER_BLOCK = 6

# Number of confirmation blocks
# Each block ~ 10 minutes
CONFIRMATION_BLOCKS = 3

# Web server port
WEB_SERVER_PORT = 65010

# Debug mode
DEBUG = False

# Log file name
LOG_FILE_NAME = 'webserver.log'







