import sqlite3
from gdds.settings import DATABASE_NAME

GET_REST_SQL = '''
SELECT * FROM tables
WHERE parent != ""
AND type = "folder"
AND location = ""
AND parent NOT IN(SELECT id from tables WHERE location = "")
'''

FOLDER_STRUCTURE = '''
CREATE TABLE IF NOT EXISTS tables (
id TEXT NOT NULL PRIMARY KEY,
title TEXT,
parent TEXT,
location TEXT,
type TEXT,
modified TEXT,
local_modified INTEGER,
ino INTEGER,
parent_ino INTEGER
)'''

TABLE_NAME = "tables"

class Database(object):

    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_NAME)
        self.cursor = self.connection.cursor()
        self.cursor.execute(FOLDER_STRUCTURE)

    def drop(self):
        self.cursor.execute("DROP TABLE tables")

    def updateResource(self, resource_id, *args):
        """
        """
        sql = self.kwargs_to_sql(dict(args[0]))
        t = tuple(sql[0] + [ resource_id])
        status = self.cursor.execute(sql[1], t)
        self.connection.commit()


    def getAll(self):
        results = self.cursor.execute("SELECT * FROM tables")

        for i in results:
            print i


        for k in results:
            print k


    def insertResource(self, *args):
        """
        """
        sql = self.kwargs_to_sql(dict(args[0]), type="insert")
        t = tuple(sql[0])
        status = self.cursor.execute(sql[1], t)
        self.connection.commit()

    def getRest(self):
        """
        """
        status = self.cursor.execute(GET_REST_SQL).fetchall()
        return status

    def getLocation(self, id):
        """
        """
        status = self.cursor.execute('SELECT * FROM tables where id = ?', (id,)).fetchone()
        print status
        return status

    def getDetails(self, detail, key):
        status = self.cursor.execute("SELECT " + detail + " FROM tables WHERE id=?", (key,)).fetchone()
        if status:
            return status
        else: return False

    def getDetailsByIno(self, detail, key):
        status = self.cursor.execute("SELECT " + detail + " FROM tables WHERE ino=?", (key,)).fetchone()
        if status:
            return status
        else: return False

    def resourceExists(self, ino):
        """
        """
        status = self.cursor.execute("SELECT ino FROM tables WHERE ino=?", (ino,)).fetchone()
        if status is not None:
            return status
        else: return None

    def getKeyByIno(self, ino):
        """
        """
        status = self.cursor.execute('SELECT id FROM tables where ino = ?', (ino,)).fetchone()
        return status


    def getParentInos(self):
        """
        """
        status = self.cursor.execute('SELECT * FROM tables where parent_ino = "" and parent != "" ').fetchall()
        return status

    def deleteById(self, id):
        """
        """
        status = self.cursor.execute('DELETE FROM tables WHERE id=? ', (id,))
        self.connection.commit()
        return status

    def deleteByMultiId(self, id):
        """
        """
        status = self.cursor.execute('DELETE FROM tables WHERE parent IN(?) ', (id,))
        self.connection.commit()
        return status

    def getAllFolders(self):
        """
        """
        status = self.cursor.execute('SELECT ino,id,parent,title FROM tables where type = "folder" ').fetchall()
        return status

    def kwargs_to_sql(self, kwargs, table=TABLE_NAME, condition="id", type="update"):
        """
        """
        p, t, r, s = [], [], [], []
        if type=="update":
            for key, value in kwargs.iteritems():
                p.append(key + "=?")
                t.append(value)
            r.append(t)
            r.append("UPDATE %s SET " % table + ",".join(p) + " WHERE %s=? " % condition)
            #print r[1]
            return r
        elif type=="insert":
            for key, value in kwargs.iteritems():
                p.append(key)
                t.append(value)
                s.append("?")
            r.append(t)
            r.append("INSERT INTO %s(" % table + ",".join(p) + ") VALUES(" + ",".join(s) + ")")
            return r

    def __del__(self):
        self.cursor.close()