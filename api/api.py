from typing import Annotated, Union, List, Any, Dict
import os
import bson
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from exception_handlers import request_validation_exception_handler, http_exception_handler, unhandled_exception_handler
from dbConnection import DB as db
from pydantic import BaseModel
from passlib.context import CryptContext
from authlib.jose import jwt
from datetime import datetime, timedelta
import secrets
from operator import itemgetter

notSetupError = HTTPException(
        status_code = 399,
        detail = "App not setup",
        headers={"WWW-Authenticate": "Bearer"}, 
    )

#-----App Setup-----#
app = FastAPI()

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

#Restrict IP's to internal docker containers
origins = [
    "https://web:5000",
    "https://db:5000",
    "web:5000",
    "db:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def rebuild_db_users(root_pass):
    global dataClient
    global userClient
    root = db()
    await root.connect('admin','root', root_pass, 'system.users')
    api_pass = secrets.token_urlsafe(16)
    

    if root.passfail == True:
        if root.collection.find_one({"user":"api_user"}):
            root.client.admin.command("updateUser", "api_user", pwd=api_pass)
        else:
            root.client.admin.command("createUser", "api_user",
                pwd=api_pass,
                roles=[{"role": "readWrite", "db": os.environ.get('MONGO_DBNAME')}])
    else:
        print("ERROR: no DB connection with root password given")
        raise HTTPException(
            status_code = 401,
            detail = "Root password not correct",
            headers={"WWW-Authenticate": "Bearer"}, 
        )
    os.environ["API_USER_PASS"] = api_pass

    dataClient = db()
    userClient = db()
    await dataClient.connect(os.environ.get('MONGO_DBNAME'), 'api_user', os.environ.get('API_USER_PASS'), 'data')
    await userClient.connect(os.environ.get('MONGO_DBNAME'), 'api_user', os.environ.get('API_USER_PASS'), 'users')

@app.on_event("startup")
async def configure_db_and_routes():
    global dataClient
    global userClient
    os.environ["SETUP"] = "True"

    #Attempts to connect with default root pass. If successful, trigger root change pass screen. Should fail if not first time startup
    rootClient = db()
    await rootClient.connect('admin','root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')

    if not rootClient.passfail:
        os.environ["SETUP"] = "False"


    if os.environ["SETUP"] == "True":
        await rebuild_db_users(os.environ.get('ROOT_MONGO_PASSWORD'))

    #Connect API users with auto-generated pass
    dataClient = db()
    userClient = db()
    await dataClient.connect(os.environ.get('MONGO_DBNAME'), 'api_user', os.environ.get('API_USER_PASS'), 'data')
    await userClient.connect(os.environ.get('MONGO_DBNAME'), 'api_user', os.environ.get('API_USER_PASS'), 'users')
    

async def setup(root_password):
    rootClient = db()
    await rootClient.connect('admin','root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')

    if not rootClient.passfail:
        print("Error: Failed to set root pass:")
        raise HTTPException(
            status_code = 401,
            detail = "ERROR: Default pass not working. Something went wrong",
        )

    rootClient.client.admin.command("updateUser", "root", pwd=root_password)

    oldRootClient = db()
    await oldRootClient.connect('admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')

    if oldRootClient.passfail:
        print("Error: Failed to update root password")
        raise HTTPException(
            status_code = 500,
            detail = "Error: Failed to update root password"
        )
    else:
        os.environ["SETUP"] = "False"
        print("Database root pass change success!")

    await rebuild_db_users(root_password)

    return True

#-----Models-----#
class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterForm(BaseModel):
    username: str
    email: str
    password: str


class TokenData(BaseModel):
    username: str | None = None

class UserCategory(BaseModel):
    category: str
    icon: str
    color: str

class UserAttribute(BaseModel):
    attribute_name: str
    datatype: str
    category: str

class User(BaseModel):
    username: str
    email: str | None = None
    roles: List[str] | None = None
    attributes: List[UserAttribute] | None = None
    categories: List[UserCategory]
    settings: List[str] | None = None
    disabled: bool | None = None



class UserInDB(User):
    hashed_password: str


class ErrorResponse(BaseModel):
    detail: str

class DataPoint(BaseModel):
    data: Any
    timestamp: datetime

    class Config:
        extra = 'allow'

class DataArray(BaseModel):
    attribute_name: str
    data_array: List[DataPoint]




#-----Auth-----#
# using the following pages as a guide 
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# https://www.mongodb.com/developer/languages/python/farm-stack-authentication/

#Should generate new JWT token on runtime rather than having to store the token in an open source repo
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
     return pwd_context.verify(plain_password.encode('utf-8'), hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password.encode('utf-8'))


def get_user(username: str):
    global userClient
    col = userClient.collection

    return col.find_one({'username':username})


def authenticate_user(username: str, password: str):
    user = get_user(username)
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
    rootClient = db()
    await rootClient.connect('admin','root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')

    if rootClient.passfail:
        raise notSetupError
    
    dataClient = db()
    await dataClient.connect(os.environ.get('MONGO_DBNAME'),'api_user', os.environ.get('API_USER_PASS'), 'data')
    
    if not dataClient.passfail:
        print("App needs rebuild:")
        raise HTTPException(
            status_code = 398,
            detail = "App needs to be rebuilt",
            headers={"WWW-Authenticate": "Bearer"}, 
        )

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
    except Exception as e:
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

async def register(username, password, email):
    global userClient
    userCol = userClient.collection

    res = userCol.find_one({"$or": [{"username":username}, {"email":email}] })

    if res:
        raise HTTPException(
        status_code = 409,
        detail = "Username or email already exists",
        headers={"WWW-Authenticate": "Bearer"}, 
    )

    userCol.insert_one({
                    'username':username,
                    'email':email,
                    'joinDateTime':datetime.now(),
                    'password_hash':get_password_hash(password),
                    'disabled':False,
                    'roles':[],
                    'categories':[
                        {'category':"basic"       , 'icon':"UilHeart"     , 'color':"#d10a0a"},
                        {'category':"health"      , 'icon':"UilHeart"     , 'color':"#fcba03]"},
                        {'category':"body"        , 'icon':"UilWeight"    , 'color':"blue]"   },
                        {'category':"food"        , 'icon':"UilPizzaSlice", 'color':"green]"  },
                        {'category':"fitness"     , 'icon':"UilDumbbell"  , 'color':"violet]" },
                        {'category':"mental"      , 'icon':"UilHeart"     , 'color':"#878787]"},
                        {'category':"productivity", 'icon':"UilClock"     , 'color':"black"  },
                    ],
                    'attributes':[
                        {'attribute_name':'weight' ,'datatype':'float'  ,'category':'body'  ,'widget':'int-decgood'},
                        {'attribute_name':'age'    ,'datatype':'int'    ,'category':'basic' ,'widget':'int'},
                        {'attribute_name':'mood'   ,'datatype':'int'    ,'category':'mental','widget':'scale-ten'},
                        {'attribute_name':'journal','datatype':'journal','category':'mental','widget':'text-long'}
                    ],
                    'settings':[]
                    })
    
    return authenticate_user(username, password)

#-----Get data-----#
async def getDataArray(attributeName, user):
    global dataClient
    dataCol = dataClient.collection

    res = dataCol.find({"$and": [{"attribute_name":attributeName}, {"username":user['username']}]})

    if not res:
        return {"attribute_name":attributeName, "data_array":[]}

    resArr = []
    for doc in res:
        resArr.append(doc)

    newlist = sorted(resArr, key=itemgetter('startTimeDate')) 


    bigArr = []

    for dataArray in newlist:
        bigArr.extend(dataArray["datapoints"])

    return {"attribute_name":attributeName, "data_array":bigArr}

#-----Utility Functions-----#
def cursorToDict(cursor):
    if not cursor or isinstance(cursor, dict): return cursor
 
    return dict(zip(zip(*cursor.description)[0], cursor.fetchone()))


#-----Set data-----#
async def createDataAttribute(attributeName, user):
    global dataClient
    dataCol = dataClient.collection


    doc = dataCol.insert_one({
            "username":user['username'],
            "attribute_name":attributeName,
            "next_document":"",
            "datapoints":[],
            "startTimeDate":datetime.now(),
            "endTimeDate":datetime.now()
        })
    return doc.inserted_id

async def setDatapoint(attributeName, user, data):
    global dataClient
    dataCol = dataClient.collection

    #datapoint = {"timestamp":datetime.now(), "data":data}

    res = cursorToDict(dataCol.find_one({"$and": [{"attribute_name":attributeName}, {"username":user['username']}]}))

    if res:
        if res['next_document']:
            while True:
                res = cursorToDict(dataCol.find_one({"_id":res['next_document']}))
                
                if not res['next_document']:
                    break
    else:
        id = await createDataAttribute(attributeName, user)
        res = cursorToDict(dataCol.find_one({"_id":id}))

    #Create new document and link old document when larger than 10 mb

    #print(res)
    if len(bson.BSON.encode(res)) > 10000000:
        id = await createDataAttribute(attributeName, user)
        id = id
        dataCol.update({"_id":res['_id']}, {"next_document":id})
        res = cursorToDict(dataCol.find_one({"_id":id}))


    dataCol.update_one(
        {"_id": res["_id"]},
        {
            '$push': {'datapoints': {"timestamp": datetime.now(), "data": data}},
            '$set': {"endDateTime": datetime.now()}
        }
    )


#-----User Functions-----#

async def setUserAttribute(attribute_name, datatype, category, widget, current_user):
    global userClient
    userCol = userClient.collection
    if any(attribute_name in d for d in current_user["attributes"]):
        raise HTTPException(
            status_code = 409,
            detail = "Attribute already exists"
        )
    userCol.update_one(
        {'username':current_user["username"]},
        {'$push': {'attributes': {'attribute_name':attribute_name,'datatype':datatype,'category':category,'widget':widget}}}
    )

#-----API endpoints-----#
    

#Auth and setup routes
@app.post("/token", response_model=Union[Token, ErrorResponse])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):

    if os.environ["SETUP"] == "True":
        return notSetupError
    

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


@app.post("/register", response_model=Union[Token, ErrorResponse])
async def register_and_get_token(username: Annotated[str, Form()], password: Annotated[str, Form()], email: Annotated[str, Form()]):
    if os.environ["SETUP"] == "True":
        return notSetupError

    user = await register(username, password, email)

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


@app.post("/setup/setRoot")
async def set_root_password(password: str = Form(...)):
    if os.environ["SETUP"] != "True":
        raise HTTPException(
            status_code = 400,
            detail = "App already set up"
        )
    
    await setup(password)


@app.post("/setup/rebuild")
async def set_root_password(password: str = Form(...)):
    await rebuild_db_users(password)


#User Routes

@app.get("/users/me", response_model=Union[User, ErrorResponse])
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

#User Attributes CRUD
@app.post("/users/newAttribute")
async def newAttribute(attribute_name: Annotated[str, Form()], datatype:Annotated[str, Form()], category:Annotated[str, Form()], widget:Annotated[str, Form()],current_user: Annotated[User, Depends(get_current_active_user)]):

    await setUserAttribute(attribute_name, datatype, category, widget, current_user)

#Data routes
@app.get("/get/{attrName}",response_model=Union[DataArray, ErrorResponse])
async def getData(attrName, current_user: Annotated[User, Depends(get_current_active_user)]):

    dataArr = await getDataArray(attrName,current_user)

    return dataArr



@app.get("/getMany",response_model=Union[dict[str, list[DataArray]], ErrorResponse])
async def getMuchData( current_user: Annotated[User, Depends(get_current_active_user)], a: Annotated[list[str], Query()] = []):
    result = []
    if(a):
        for attr in a:
            arr = await getDataArray(attr,current_user)
            if arr:
                result.append(arr)
            else:
                result.append({"attribute_name": attr, "data_array":[] })
                
    return {"data": result}


@app.post("/set")
async def setData(attribute_name: Annotated[str, Form()], datapoint:Annotated[Any, Form()], current_user: Annotated[User, Depends(get_current_active_user)]):
    print(attribute_name, current_user, datapoint)
    await setDatapoint(attribute_name, current_user, datapoint)
