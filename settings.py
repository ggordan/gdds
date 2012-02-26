CONSUMER_KEY = '71362387555.apps.googleusercontent.com'
CONSUMER_SECRET = 'vKYSJlFYJ3qrJuO_Uj6bqolJ'
CALLBACK_URL = "urn:ietf:wg:oauth:2.0:oob"
USER_AGENT = "Gdata-Desktop-Sync"

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

 # /media/Media/Dropbox/Programming/Python/projects/gdds/bin