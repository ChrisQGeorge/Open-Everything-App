from flask import Flask
from pymongo import MongoClient
import os

app = Flask(__name__)

mongo_username = os.environ.get('MONGO_USERNAME')
mongo_password = os.environ.get('MONGO_PASSWORD')
mongo_dbname = os.environ.get('MONGO_DBNAME')

try:
    client = MongoClient(f"mongodb://{mongo_username}:{mongo_password}@db:27017/{mongo_dbname}")
    db = client[mongo_dbname]
    collection = db["data"]
except:
    pass

try:
    res = collection.find_one({"_id": 1})

    if not res:
        collection.insert_one(
            { "_id": 1, "data":"Hello world from MongoDB!"}
        )
except:
    pass




@app.route('/')
def hello_world():
    data = {}
    try:
        data = collection.find_one({"_id": 1})
    except:
        pass
    if not data:
        data = {'data':'ERROR'}
    return {'message':data["data"]}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')