from gdds.settings import SYNC_DIRECTORY, DATABASE_NAME
from os import path, stat, mkdir, remove
from gdds.gdds.database import Database as db
import re
from time import sleep

class Initialize(object):

    q_string = "(folder%3.*)"
    parent_key = "root"
    file_path = ""
    resource = None

    def __init__(self, client):
        self.client = client

    def _init_sync(self):
        self._env_check() # create env
        self._init_fetch_folders()
        self._init_fetch_documents()

    Start = _init_sync

    def _init_fetch_folders(self):

        # Fetch all the 'collections' from Google Documents
        folders = self.client.GetResources(uri='/feeds/default/private/full/-/folder')

        # Iterate through all folders
        for self.resource in folders.entry:

            data = {
                'id' : self.resource.resource_id.text,
                'title' : self.resource.title.text,
                'location' : '',
                'type' : 'folder',
                'ino' : '',
                'parent' : self.get_parent(self.resource),
                'parent_ino' : self.get_parent_ino(self.get_parent(self.resource))
            }

            # if the document has no parent, set file path to root directory
            if data['parent'] == "":
                self.file_path = SYNC_DIRECTORY + self.resource.title.text + "/"
                data['location'] = self.file_path

                # create the folder if it doesn't exist
                if not path.exists(self.file_path):
                    mkdir(self.file_path)

                # get the new folder inode
                data['ino'] = stat(self.file_path).st_ino
                # insert folder reference to database
                db().insertResource(data)
            else:
                # Insert a reference only to the database for non-root folders
                db().insertResource(data)

            self.file_path = ""
            # Now add all the other folders

        #  Create the referenced folders (nested)
        while db().getRest():
            upd_data = {} # reset update data

            for row in db().getRest():
                upd_data['location'] = self.get_location(row[0], row[1])

                if not path.exists(upd_data['location']):
                    mkdir(upd_data['location'])

                upd_data['ino'] = stat(upd_data['location']).st_ino
                upd_data['parent_ino'] = self.get_parent_ino(row[2])
                db().updateResource(row[0], upd_data)

    def _init_fetch_documents(self):

        documents = self.client.GetResources(uri='/feeds/default/private/full')
        from os.path import getmtime

        for document in documents.entry:
            sleep(1)

            # check if the document has slashes in its name
            doctype = re.search("(\w*(?=:))", document.resource_id.text).group(0)

            # add functionality for tables later on
            if doctype != "table":

                data = {
                    'id' : document.resource_id.text,
                    'title' : document.title.text,
                    'modified' : document.updated.text,
                    'type' : doctype,
                    'location' : '',
                    'parent' : self.get_parent(document),
                    'parent_ino' : self.get_parent_ino(self.get_parent(self.resource))
                }

                fileExtension = self.fileType(doctype)

                if document.InCollections():

                    fileLocation = db().getLocation(data['parent'])[3] + unicode(document.title.text).replace('/', '\\') +  fileExtension

                    if not path.exists(fileLocation):
                        if self.fileType(doctype) != "":
                            self.client.DownloadResource(document, fileLocation, \
                                extra_params={'exportFormat': fileExtension[1:]})
                        else:
                            self.client.DownloadResource(document, fileLocation)

                    data['ino'] = stat(fileLocation).st_ino
                    data['local_modified'] = int(getmtime(fileLocation))
                    db().insertResource(data)
                else:
                    fileLocation = SYNC_DIRECTORY + unicode(document.title.text).replace('/', '\\') + fileExtension

                    if self.fileType(doctype) != "":
                        self.client.DownloadResource(document, fileLocation, \
                            extra_params={'exportFormat': fileExtension[1:]})
                    else:
                        self.client.DownloadResource(document, fileLocation)

                    data['ino'] = stat(fileLocation).st_ino
                    data['local_modified'] = int(getmtime(fileLocation))
                    db().insertResource(data)

    def fileType(self, type):
        try:
            return {
                'spreadsheet' : '.xls',
                'document' : '.doc',
                'presentation' : '.ppt',
                }[type]
        except KeyError as NotInIndex:
            return ""

    def get_parent(self, resource):
        if resource.InCollections():
            return re.search(self.q_string, resource.InCollections()[0].href.strip()).group(0).replace("%3A", ":")
        else: return ""

    def get_parent_ino(self, parent_key):
        file_location = self.get_location(parent_key, "")
        if path.exists(file_location):
            return stat(file_location).st_ino
        else: return ""

    def _env_check(self):
        if path.exists(DATABASE_NAME):
            remove(DATABASE_NAME)
        return False

    def get_location(self, id, resource_title):

        if id=="":
            return SYNC_DIRECTORY + "/%s/" % resource_title
        else:
            location = []
            docDetail = db().getDetails("parent, title", id)
            if docDetail:
                if resource_title == "":
                    resource_title = docDetail[1]
                while db().getDetails("parent, title", docDetail[0]):
                    docDetail = db().getDetails("parent, title", docDetail[0])
                    location.append(docDetail[1])
            else:
                return ""

            return SYNC_DIRECTORY + "/".join(location[::-1]) + "/%s/" % resource_title
