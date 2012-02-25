from gdds import settings
import gdata.gauth
import webbrowser
from time import sleep
from sys import exit
from os import path
import gdata.docs

def auth():

    token = False
    counter = 1
    getAuth = webbrowser.get()

    if path.exists(".token"):
        settings.REFRESH_TOKEN = open(".token", "r").readline()

    while not token:

        if not settings.REFRESH_TOKEN:

            authenticated = False
            print settings.REFRESH_TOKEN

            OAuth = gdata.gauth.OAuth2Token(
                client_id=settings.CONSUMER_KEY,
                client_secret=settings.CONSUMER_SECRET,
                scope=settings.SCOPES,
                user_agent=settings.USER_AGENT
            )

            # To avoid having to authorize the user constantly, pass the access_type and approval_prompt kwargs
            # Source for the change: http://googleappsdeveloper.blogspot.com/2011/10/upcoming-changes-to-oauth-20-endpoint.html
            print "\n" +OAuth.generate_authorize_url( access_type = "offline", approval_prompt = "force") + "\n"

            getAuth.open(OAuth.generate_authorize_url( access_type = "offline", approval_prompt = "force"))
            sleep(2)

            while not authenticated:
                try:
                    var = raw_input("Enter your code here: ")
                    OAuth.get_access_token(var)
                    authenticated, token = True, True

                    # store the refresh token
                    f=open(".token", "w+").write(OAuth.refresh_token)
                    settings.REFRESH_TOKEN = OAuth.refresh_token

                except gdata.gauth.OAuth2AccessTokenError:
                    if counter>2:
                        exit(" \n Sorry, there was a problem connecting to your Google Docs account. Not sure why \n")
                    else:
                        print " \n There was a problem authenticating with the code you provided. Please enter the code again \n "
                        counter+=1
                except KeyboardInterrupt: exit(" \n Cya! ")
        else:

            OAuth = gdata.gauth.OAuth2Token(
                client_id=settings.CONSUMER_KEY,
                client_secret=settings.CONSUMER_SECRET,
                scope=settings.SCOPES,
                user_agent=settings.USER_AGENT,
                refresh_token=settings.REFRESH_TOKEN
            )

        # Initialise the application
        client = gdata.docs.client.DocsClient(source=settings.USER_AGENT)
        client.api_version = "3"
        client.ssl = True
        OAuth.authorize(client)

        try:
            client.GetResources(limit=1)
        except gdata.client.RequestError:
            settings.REFRESH_TOKEN = False
            print " \n Your token has expired, you need to reauthorize the app. \n"

        return OAuth
