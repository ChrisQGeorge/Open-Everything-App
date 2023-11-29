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
            print(uri)
            print(e)

        if self.passfail:
            print("connected with uri:"+uri)
            self.client = conn
            self.username = username
            self.databaseName = database
            self.db = self.client[database]
            self.collection = self.db[collection]
            return True
        
        return False
    async def changePass(self, newPass, adminClient):
        
        response = adminClient.admin.command("updateUser", self.username, pwd=newPass)

        print("Change pass response: " + str(response))
        time.sleep(3)

        await self.connect(self.databaseName, self.username, newPass, self.collectionName )