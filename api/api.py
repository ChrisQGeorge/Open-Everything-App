from typing import Annotated
import os
from fastapi import Depends, FastAPI, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dbConnection import DB as db
from pydantic import BaseModel
from passlib.context import CryptContext
from authlib.jose import jwt
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv

notSetupError = HTTPException(
        status_code = 399,
        detail = "App not setup",
        headers={"WWW-Authenticate": "Bearer"}, 
    )


#-----App Setup-----#
app = FastAPI()


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
    root = db('admin','admin', 'root', root_pass, 'system.users')
    api_pass = secrets.token_urlsafe(16)


    if root.collection.find({"user":"api_user"}):
        try:
            root.database.command("updateUser", "root", pwd=api_pass)
        except Exception as e:
            print(f"Error creating MongoDB user: {e}")

    else:
        try:
            root.db.command("createUser", "api_user",
                            pwd=api_pass,
                            roles=[{"role": "readWrite", "db": os.environ.get('MONGO_DBNAME')}])

        except Exception as e:
            print(f"Error creating MongoDB user: {e}")

    # Writing to .env file
    try:
        with open('.env', 'a') as file:
            file.write(f"API_USER_PASS={api_pass}\n")
        print(f"Successfully wrote API_USER_PASS to .env")
    except IOError as error:
        print(f"An error occurred while writing to .env: {error}")


@app.on_event("startup")
async def configure_db_and_routes():
    global rootClient
    global dataClient
    global userClient

    os.environ["SETUP"] = "True"

    #Attempts to connect with default root pass. If successful, trigger root change pass screen. Should fail if not first time startup
    try:
        rootClient = db('admin',  'admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')
        rootCleint.collection.find_one()
    except:
        os.environ["SETUP"] = "False"

    if os.environ["SETUP"] == "True":
        await rebuild_db_users(os.environ.get('ROOT_MONGO_PASSWORD'))

    load_dotenv()

    dataClient = db(os.environ.get('MONGO_DBNAME'), os.environ.get('MONGO_DBNAME'), 'root', os.environ.get('API_USER_PASS'), 'data')
    userClient = db(os.environ.get('MONGO_DBNAME'), os.environ.get('MONGO_DBNAME'), 'root', os.environ.get('API_USER_PASS'), 'users')
    userCol = userClient.collection
    dataCol = dataClient.collection
    print(userCol)
    try:
        dataTest = dataCol.find_one({"_id":1})
 
        if not dataTest:
            dataCol.insert_one({"_id":1, 'message':"Hello world from MongoDB!"})

        userTest = userCol.find_one({"_id":1})
        print(userTest)


        if not userTest:
            userCol.insert_one({
                "_id":1,
                "username":"test",
                'password_hash':get_password_hash("test"),
                'disabled':False
                })
    except:
        pass
    
async def setup(root_password):
    try:
        rootClient = db('admin',  'admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')
        
        rootClient.db.command("updateUser", "root", pwd=root_password)
        
    except:
        print(os.environ["SETUP"])
        os.environ["SETUP"] = "False"

    try:
        rootClient = db('admin',  'admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')
        rootClient.collection.find_one()
    except:
        os.environ["SETUP"] = "False"

    await rebuild_db_users(root_password)

    return True


#-----Auth Setup-----#
# using the following pages as a guide 
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# https://www.mongodb.com/developer/languages/python/farm-stack-authentication/

#Should generate new JWT token on runtime rather than having to store the token in an open source repo
SECRET_KEY = secrets.token_urlsafe(32)
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
     return pwd_context.verify(plain_password.encode('utf-8'), hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password.encode('utf-8'))


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
    raiseError = True
    try:
        rootClient = db('admin',  'admin', 'root', os.environ.get('ROOT_MONGO_PASSWORD'), 'system.users')
        rootClient.collection.find_one()
    except:
        raiseError = False
        
    if raiseError:
        raise notSetupError
    
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
@app.post("/login", response_model=Token)
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


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.get("/setup/firstTimeStartup")
async def setup_confirm():
    return {'data':os.environ["SETUP"]}
    
@app.post("/setup/setRoot")
async def set_root_password(password: str = Form(...)):
    if os.environ["SETUP"] != "True":
        raise HTTPException(
            status_code = 400,
            detail = "App already set up"
        )
    
    await setup(password)

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
