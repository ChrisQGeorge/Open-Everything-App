from pymongo import MongoClient
import time

class DB:
    client = None
    db = None
    collection = None
    passfail = None
    username = None
    databaseName = None
    collectionName = None

    async def connect(self, database, username, password, collection):
        uri = f"mongodb://{username}:{password}@db:27017/{database}?authSource=admin"
        conn = MongoClient(uri)
        try:
            conn.server_info()
            self.passfail = True
        except Exception as e:
            self.passfail = False

        if self.passfail:
            self.client = conn
            self.username = username
            self.databaseName = database
            self.db = self.client[database]
            self.collection = self.db[collection]
            return True
        
        return False