CONSUMER_KEY = ''
CONSUMER_SECRET = ''
CALLBACK_URL = ""
USER_AGENT = "gdds"

SCOPES = " ".join([
    "https://docs.google.com/feeds/",
    "https://spreadsheets.google.com/feeds/",
    "https://docs.googleusercontent.com",
])

DATABASE_NAME = ".tables.db"
APP_DIRECTORY = ""

# directory to which to sync google docs too
SYNC_DIRECTORY = "/home/ggordan/Desktop/GoogleDocs/"
PID = APP_DIRECTORY + ".pid"

REFRESH_TOKEN = False