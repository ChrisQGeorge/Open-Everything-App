from typing import Union
import os
from pymongo import MongoClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://172.*.*.*:3000",
    "172.*.*.*:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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



@app.get("/")
def read_root():
    data = {}
    try:
        data = collection.find_one({"_id": 1})
    except:
        pass
    if not data:
        data = {'data':'ERROR'}
    
    return {'message':data["data"]}
