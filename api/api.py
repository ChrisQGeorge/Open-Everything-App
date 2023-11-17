from typing import Annotated
import os
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dbConnection import DB as db
from pydantic import BaseModel
from passlib.context import CryptContext
from authlib.jose import jwt
from datetime import datetime, timedelta
import json
firstTimeStartup = True

#-----App Setup-----#
app = FastAPI()


#Restrict IP's to internal docker containers
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
#Attempts to connect with default root pass. If successful, trigger root change pass screen. Should fail if not first time startup
#try:
#    rootClient = db('admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'))
#except:
#    firstTimeStartup = False
#dataClient = db(os.environ.get('MONGO_DBNAME'), "data", os.environ.get('MONGO_USERNAME'), os.environ.get('MONGO_PASSWORD'))
#userClient = db(os.environ.get('MONGO_DBNAME'), "users", os.environ.get('MONGO_USERNAME'), os.environ.get('MONGO_PASSWORD'))

dataClient = db('admin', os.environ.get('MONGO_DBNAME'), 'root', "CHANGEME", 'data')
userClient = db('admin', os.environ.get('MONGO_DBNAME'), 'root', "CHANGEME", 'users')

@app.on_event("startup")
async def configure_db_and_routes():
    userCol = userClient.collection
    dataCol = dataClient.collection

    dataTest = dataCol.find_one({"_id":1})

    if not dataTest:
        dataCol.insert_one({"_id":1, 'message':"Hello world from MongoDB!"})
    
    userTest = userCol.find_one({"_id":1})

    if not userTest:
        userCol.insert_one({
            "_id":1,
            "username":"test",
            'password_hash':get_password_hash("test"),
            'disabled':False})
    


#-----Auth Setup-----#
# using the following pages as a guide 
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# https://www.mongodb.com/developer/languages/python/farm-stack-authentication/

#Should generate new JWT token on runtime rather than having to store token in an open source repo
SECRET_KEY = str(uuid4())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    col = userClient.collection

    return col.find_one({'username':username})


def authenticate_user(username: str, password: str):
    user = get_user(username)
    print(user)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode({'alg':ALGORITHM}, to_encode, SECRET_KEY)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user['disabled']:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


#-----API endpoints-----#


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/")
async def read_root(token: Annotated[str, Depends(get_current_active_user)]):

    data = {}
    try:
        data = dataClient.collection.find_one({"_id": 1})
    except:
        pass
    if not data:
       data = {'data':'ERROR'}
    
    return {'message':data["message"]}
