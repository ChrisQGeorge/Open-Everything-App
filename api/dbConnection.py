from pymongo import MongoClient


class DB:
    client = None
    db = None
    collection = None

    def __init__(self, loginDatabase, database, username, password, collection):
        self.client = MongoClient(f"mongodb://{username}:{password}@db:27017/{loginDatabase}")
        self.db = self.client[database]
        self.collection = self.db[collection]

