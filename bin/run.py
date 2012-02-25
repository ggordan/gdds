#!/usr/bin/python

from gdds import settings
from gdds.gdds.oauth import auth
from gdata.docs import client
from gdds.gdds.initialize import Initialize
from sys import argv

OAuth = auth()

if OAuth:
    # Initialise the application
    client = client.DocsClient(source=settings.USER_AGENT)
    client.api_version = "3"
    client.ssl = True
    client.http_client.debug = False

    # Authorize access to documents using generated token
    OAuth.authorize(client)

if len(argv) == 2:
    if argv[1] == "init":
        Initialize(client=client).Start()