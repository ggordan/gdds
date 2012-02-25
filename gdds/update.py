import random
import shutil
import gdata
from os import path, rename, mkdir, stat, walk
from re import search
from time import sleep
from gdds.settings import SYNC_DIRECTORY
from gdds.gdds.database import Database as db
from gdata.docs.client import DocsClient
from shutil import move

class Update(object):

    tmpdir = "/tmp/"
    moved_to_tmp = False
    parent_directory = None
    parent_key = ""
    file_path = ""

    def __init__(self, client=DocsClient):
        self.client = client
        self._update_folders()
        exit()
        self._update_files()

    def _update_files(self):

        # upload the local files
        self._upload_files()
        # delete files

        documents = self.client.GetResources(uri= '/feeds/default/private/full')

        for document in documents.entry:

            file_changed_online, file_changed_offline, changed_parent = True, True, False

            documentParent = "" if not document.InCollections() else search("(folder%3.*)", \
                document.InCollections()[0].href.strip()).group(0).replace("%3A", ":")

            doctype = search("(\w*(?=:))", document.resource_id.text).group(0)
            exportFormat = None if not self.fileType(doctype) else {'exportFormat': self.fileType(doctype)[1:]}

            localData = db().getDetails("*", document.resource_id.text)

            if localData: # if document already in database
                if path.exists(localData[3]): # check if it exists locally

                    # Check for online changes
                    if document.updated.text == localData[5]: # check if the document hasn't been changed remotely
                        file_changed_online = False

                    # Check for offline changes
                    if int(path.getmtime(localData[3])) == localData[6]:
                        file_changed_offline = False

                    if file_changed_offline == True and file_changed_online == True:
                        '''
                            Handle clashes when the files are out of sync
                        '''
                        print "changed both"

                    else:
                        if file_changed_online: # if the file has been changed online
                            print "online version is newer"

                            parentFolder = None
                            # check if the file directory, or the file name has been changed
                            # if it has query database to check for parentDirectory
                            if documentParent != localData[2] or document.title.text != localData[1]:
                                # check if the parent exists locally
                                file_changed = True

                                if documentParent:
                                    try:
                                        parentFolder = db().getDetails('location', documentParent)[0]
                                    except TypeError:
                                        # create folder
                                        parentFolder = "new"
                                else:
                                    parentFolder = "root"
                            else:
                                self.parent_directory = localData[3]
                                file_changed = False

                            print parentFolder
                            exit()
                            if file_changed:
                                if documentParent != localData[2]:
                                    if parentFolder:
                                        if parentFolder == "":
                                            self.parent_directory = SYNC_DIRECTORY
                                        else:
                                            self.parent_directory = parentFolder
                                    else:
                                        self.parent_directory = self.tmpdir
                                        self.moved_to_tmp = True

                                    self.parent_directory += document.title.text + self.fileType(doctype)
                                else:
                                    self.parent_directory = parentFolder + document.title.text + self.fileType(doctype)

                            # the moving and doing a whateva of ze file

                            if not file_changed:
                                # if only the contents of the file have changed
                                # download the resource
                                self.client.DownloadResource(document, self.parent_directory, extra_params=exportFormat)
                                # update the database
                                localtime = int(path.getmtime(localData[3]))
                                database.updateDocument(document.resource_id.text, localData[1], documentParent, self.parent_directory, doctype,  document.updated.text, localtime)
                            else:
                            # if the file parent directory exists locally
                                print "Move file to its new directory"
                                rename(localData[3], self.parent_directory)
                                # download the resource
                                sleep(1) # delay, not sure if needed
                                self.client.DownloadResource(document, self.parent_directory, extra_params=exportFormat)
                                localtime = int(path.getmtime(self.parent_directory))
                                database.updateDocument(document.resource_id.text, localData[1], documentParent, self.parent_directory, doctype,  document.updated.text, localtime)

                        else:
                            print "file up to date"

                        if file_changed_offline:
                            print "offline version is newer"
            sleep(1)

    def _update_folders(self):
        """
        """

        # upload newly created local folders
        self._upload_folders()

        # delete locally removed folders
        #self._delete_folders()
        #sleep(1)

        # Fetch all the 'collections' from Google Documents
        folders = self.client.GetResources(uri='/feeds/default/private/full/-/folder')

        # Iterate through all folders ( All items are Resource objects )
        for resource in folders.entry:

            print "-------------------------------------------------------------"
            print "Checking Folder: %s" % resource.title.text
            # If a folder is a reference only, it means its parent doesn't exist locally yet
            reference_only, resource_changed, insert_reference = False, False, False

            # get the local data for folder
            localData = db().getDetails("*", resource.resource_id.text)

            # Set the folder parent if one exists
            self.parent_key = "" if not resource.InCollections() else \
            search("(folder%3.*)", resource.InCollections()[0].href.strip()).group(0).replace("%3A", ":")

            #print "Location parent: %s \n\n" % self.get_location(resource.resource_id.text, resource.title.text)

            # data to be inserted/updated
            data = {
                "id" : resource.resource_id.text,
                "title" : resource.title.text,
                "parent" : self.parent_key,
                "type" : "folder",
            }

            # if the folder exists locally
            if localData:

                print "Folder '%s' exists locally" % data['title']

                # check whether the folder has moved directories/changed name
                parent_changed = True if self.parent_key != localData[2] else False
                title_change = True if resource.title.text != localData[1] else False

                # if any changes were made to a file
                if parent_changed or title_change:

                    oldLocation = self.get_location(localData[2], localData[1])
                    locationParent = self.get_location(self.parent_key, "")
                    print oldLocation
                    print locationParent
                    # check whether to only create a reference

                    if not locationParent and self.parent_key != "":
                        reference_only = True
                        data['location'] = ""
                    else:
                        data['location'] = resource.title.text

                    if not reference_only:
                        try:
                            move(oldLocation, locationParent)
                        except shutil.Error as E:
                            print E
                            pass

                    db().updateResource(resource.resource_id.text, data)
            else:
                # Create the new folders
                self.file_path = self.get_location(self.parent_key, resource.title.text, files=True)
                parentAlive = db().getDetails("location", self.parent_key)

                if self.parent_key != "":
                    if not parentAlive:
                        reference_only = True
                        self.file_path = ""
                    else:
                        if parentAlive[0] == "":
                            reference_only = True
                            self.file_path = ""

                print "File location: '%s'" % self.file_path

                if not reference_only:
                    if not path.exists(self.file_path):
                        mkdir(self.file_path)

                    data['location'] = self.file_path
                    data['ino'] = stat(self.file_path).st_ino
                    data['parent_ino'] = self.get_parent_ino(self.parent_key)
                    db().insertResource(data)
                else:
                    # update database with parent key
                    data['location'] = ""
                    db().insertResource(data)

            self.parent_key = ""
            self.file_path = ""

        #  Create the rest of the folders in db
        while db().getRest():
            upd_data = {} # stores the k/v data to be updated
            for row in db().getRest():

                upd_data['location'] = self.get_location(row[0], row[1])

                if not path.exists(upd_data['location']):
                    mkdir(upd_data['location'])

                upd_data['ino'] = stat(upd_data['location']).st_ino
                upd_data['parent_ino'] = self.get_parent_ino(row[2])
                db().updateResource(row[0], upd_data)

    def get_location(self, id, resource_title, files=False):

        if id=="":
            return SYNC_DIRECTORY + "%s/" % resource_title
        else:
            location = []
            docDetail = db().getDetails("parent, title", id)

            if docDetail:
                if files:
                    location.append(docDetail[1])
                if resource_title == "":
                    resource_title = docDetail[1]
                while db().getDetails("parent, title", docDetail[0]):
                    docDetail = db().getDetails("parent, title", docDetail[0])
                    location.append(docDetail[1])
            else:
                return ""

            print location

            return SYNC_DIRECTORY + "/".join(location[::-1]) + "/%s/" % resource_title


    def _delete_folders(self):
        """
        """
        lst, tmp, ids, to_delete = self._get_all_inos(), [], [], []

        stored_folders = db().getAllFolders()
        if stored_folders:
            for folder in stored_folders:
                if folder[0] not in lst:
                    tmp.append({
                      'ino' : folder[0],
                      'id'  : folder[1],
                      'parent' : folder[2],
                      'title' : folder[3]
                    })
                    ids.append(folder[1])

        for i in tmp:
            if i['parent'] not in ids or i['parent'] == "":

                # these are the items that need to be deleted
                entry = self.client.GetResourceById(i['id'])



                self.client.DeleteResource(entry, force=True)
            db().deleteById(i['id'])

        # delete all the children
        if ids:
            db().deleteByMultiId(",".join(ids))

        sleep(5) # there tends to be some lag

    # To delete the parent, get the file whos id does not appear in parent list

    def _upload_folders(self):
        """
        """

        from gdata.docs import data as gd
        lst = self._get_all_folders()

        for resource in lst:
            data = {}

            resource_exists = db().resourceExists(resource['ino'])

            # check if the resource exists locally, and if it does check for changes
            if resource_exists:

                print "Resource: '%s' : already exists" % resource['title']

                # check if the location of the file has changed
                localData = db().getDetailsByIno("*", resource['ino'])

                # if the folder location has changed
                if resource['parent_ino'] != localData[8]:

                    print "Modifying existing folder: %s" % resource['title']

                    parent_key = db().getDetailsByIno("*", resource['parent_ino'])

                    if parent_key:
                        data['parent_ino'] = resource['parent_ino']
                        data['title'] = resource['title']
                        data['ino'] = resource['ino']
                        data['parent'] = db().getKeyByIno(resource['parent_ino'])
                        if data['parent']:
                            data['parent'] = data['parent'][0]
                        else: data['parent'] = ""

                        print "Parent key: %s" % parent_key[0]
                        print "Resource key: %s " % localData[0]

                        resourceToMove = self.client.GetResourceById(localData[0])
                        collection = self.client.GetResourceById(parent_key[0])
                        self.client.MoveResource(resourceToMove, collection=collection)
                        db().updateResource(localData[0], data)
                    else:
                        lst.append(resource); continue

                elif resource['title'] != localData[1]:
                    """
                        If the folder name only changes
                    """
                    print "Folder '%s' has been renamed" % resource['title']

                    entry = self.client.GetResourceById(localData[0])
                    entry.title.text = resource['title']
                    data['title'] = resource['title']
                    self.client.UpdateResource(entry)
                    db().updateResource(localData[0], data)
            else:
                print "Creating a new folder: %s " % resource['title']

                # check if the folder is in the root directory
                if resource['parent_location'] == SYNC_DIRECTORY[:-1]:
                    data['parent'] = ""
                    data['location'] = ""
                    data['parent_ino'] = stat(SYNC_DIRECTORY).st_ino
                else:

                    data['parent'] = db().getKeyByIno(resource['parent_ino'])

                    if not data['parent']:
                        lst.append(resource)
                        continue
                    else:
                        data['parent'] = data['parent'][0]

                    data['location'] = self.get_location(data['parent'], resource['title'])

                data['ino'] = resource['ino']
                data['title'] = resource['title']
                data['type'] = "folder"
                data['parent_ino'] = self.get_parent_ino(data['location'])
                collection = self.client.GetResourceById(data['parent'])
                newResource = gd.Resource(gd.COLLECTION_LABEL, resource['title'])
                # create a new folder
                newFolder = self.client.CreateResource(newResource, collection=collection)
                data['id'] = newFolder.resource_id.text
                db().insertResource(data)

    def _upload_files(self):
        """
        """
        from gdata.docs import data as gd
        from gdds.magic.magic import Magic
        lst = self._get_all_files()

        for file in lst:

            data = {}
            dbStatus = db().resourceExists(file['ino'])

            if dbStatus:
                print "File: %s : exists" % file['title']
                # check if the location of the file has changed
                localData = db().getDetailsByIno("*", file['ino'])
                fileTitle = file['title'].split(".")[0]
                data['location'] = fileTitle

                if file['parent_ino'] != localData[8]:

                    if file['parent_location'] == SYNC_DIRECTORY[:-1]:
                        data['parent'] = ""
                    else:
                        data['parent'] = db().getKeyByIno(file['parent_ino'])

                        if data['parent']:
                            data['parent'] = data['parent'][0]

                    print "Modifying existing folder: %s" % file['title']

                    data['parent_ino'] = file['parent_ino']
                    data['title'] = file['title']
                    data['ino'] = file['ino']
                    if data['parent']:
                        data['parent'] = data['parent'][0]
                    else: data['parent'] = ""

                    resourceToMove = self.client.GetResourceById(localData[0])
                    try:
                        collection = self.client.GetResourceById(data['parent'])
                    except gdata.client.RequestError: collection = None
                    self.client.MoveResource(resourceToMove, collection=collection)
                    db().updateResource(localData[0], data)

                elif file['title'] != localData[1]:
                    """
                        If the file name only changes
                    """
                    entry = self.client.GetResourceById(localData[0])
                    entry.title.text = fileTitle
                    data['title'] = fileTitle
                    self.client.UpdateResource(entry)
                    db().updateResource(localData[0], data)
            else:

                print "Creating a new file: %s " % file['title']

                fileTitle = file['title'].split(".")[0]
                mime = Magic(mime=True).from_file(file['location'])

                if mime == "application/zip":
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif mime == "application/vnd.ms-office":
                    mime = "application/vnd.ms-excel"
                # add functionality to import Pages

                # check if the folder is in the root directory
                if file['parent_location'] == SYNC_DIRECTORY[:-1]:
                    data['parent'] = ""
                    data['location'] = fileTitle
                    data['parent_ino'] = stat(SYNC_DIRECTORY).st_ino
                else:

                    data['parent'] = db().getKeyByIno(file['parent_ino'])

                    if not data['parent']:
                        data['parent'] = ""
                    else: data['parent'] = data['parent'][0]

                    data['location'] = self.get_location(data['parent'], file['title'], files=True)
                    print data['location']

                data['ino'] = file['ino']
                data['title'] = file['title']
                data['type'] = mime
                data['parent_ino'] = self.get_parent_ino(data['location'])

                filePath = file['location']
                newResource = gdata.docs.data.Resource(filePath, fileTitle)

                media = gdata.data.MediaSource()
                media.SetFileHandle(filePath, mime)

                try:
                    collection = self.client.GetResourceById(data['parent'])
                except gdata.client.RequestError: collection = None

                try:
                    newDocument = self.client.CreateResource(newResource, media=media, collection=collection)
                    data['id'] = newDocument.resource_id.text
                    db().insertResource(data)
                except gdata.client.RequestError:
                    print "There was a problem uploading: %s " % data['title']
                    pass

    def _create_folder(self):
        """
        """

    def UploadWithExponentialBackoff(self, entry):
        for n in range(0, 5):
            try:
                response = self.client.GetResources()
                return response
            except:
                sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        return None

    def _get_all_folders(self):
        lst = []
        for root, dirs, files in walk(SYNC_DIRECTORY[:-1], topdown=False):
            for name in dirs:
                lst.append(
                        {
                        "title" : name,
                        "location" : path.join(root, name),
                        "ino"   : stat(path.join(root, name)).st_ino,
                        "parent_location" : root,
                        "parent_ino"    : stat(root).st_ino
                    }
                )
        return lst

    def _get_all_files(self):
        lst = []
        for root, dirs, files in walk(SYNC_DIRECTORY[:-1], topdown=False):
            for name in files:
                lst.append(
                        {
                        "title" : name,
                        "location" : path.join(root, name),
                        "ino"   : stat(path.join(root, name)).st_ino,
                        "parent_location" : root,
                        "parent_ino"    : stat(root).st_ino
                    }
                )
        return lst

    def _get_all_inos(self):
        d, l = self._get_all_folders(), []
        for i in d:
            l.append(i['ino'])
        return l

    def get_parent_ino(self, parent_key):
        file_location = self.get_location(parent_key, "")
        if path.exists(file_location):
            return stat(file_location).st_ino
        else: return ""

    def fileType(self, type):
        try:
            return {
                'spreadsheet' : '.xls',
                'document' : '.doc',
                'presentation' : '.ppt',
                }[type]
        except KeyError as NotInIndex:
            return None