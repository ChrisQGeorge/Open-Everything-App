from flask import Flask
from pymongo import MongoClient
import os

app = Flask(__name__)

mongo_username = os.environ.get('MONGO_USERNAME')
mongo_password = os.environ.get('MONGO_PASSWORD')
mongo_dbname = os.environ.get('MONGO_DBNAME')

client = MongoClient("mongodb://"+mongo_username+":"+mongo_password+"@db:27017/admin)")
db = client[mongo_dbname]
collection = db["data"]

try:
    res = collection.find_one({"_id": 1})
except:
    collection.insert_one(
         { "_id": 1, "data":"Hello world from MongoDB!"}
    )




@app.route('/')
def hello_world():
    data = collection.find_one({"_id": 1})
    return {'message':data["data"]}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')