from typing import Annotated, Union, List, Any, Dict
import os
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from passlib.context import CryptContext
from authlib.jose import jwt
from operator import itemgetter
import secrets
import json   # Might use JSON for storing arrays in MySQL

# -- We import our MySQL-based DB class:
from dbConnection import DB as db

# -- Custom exception handlers (if you keep them):
from exception_handlers import (
    request_validation_exception_handler, 
    http_exception_handler, 
    unhandled_exception_handler
)

notSetupError = HTTPException(
    status_code=399,
    detail="App not setup",
    headers={"WWW-Authenticate": "Bearer"},
)

app = FastAPI()

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Restrict IP's to internal docker containers
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

# Globals
dataClient = None
userClient = None

# --------- Models --------- #
class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterForm(BaseModel):
    username: str
    email: str
    password: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    roles: List[str] | None = None
    attributes: List[str] | None = None
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
    attr_name: str
    data_array: List[DataPoint]


# --------- Auth & Security --------- #
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password.encode('utf-8'), hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode({'alg': ALGORITHM}, to_encode, SECRET_KEY)
    return encoded_jwt

# --------- Database Utility Functions --------- #

async def create_mysql_user_if_not_exists(root_db: db, user_name: str, user_pass: str):
    """
    Naive approach to create or update a MySQL user + grant privileges.
    In real usage, you'd carefully handle user creation, revokes, etc.
    """
    try:
        # Attempt to create user
        root_db.cursor.execute(f"CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_pass}';")
        root_db.cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {root_db.databaseName}.* TO '{user_name}'@'%';")
        root_db.cursor.execute("FLUSH PRIVILEGES;")
        root_db.connection.commit()
    except Exception as e:
        print(f"Error creating MySQL user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creating/updating MySQL user"
        )

# --------- Rebuild DB Users --------- #
async def rebuild_db_users(root_pass):
    global dataClient
    global userClient

    # 1. Connect as root to MySQL
    root = db()
    await root.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),  # Database name (analogous to 'admin')
        'root',
        root_pass,
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

    if not root.passfail:
        print("ERROR: no DB connection with root password given")
        raise HTTPException(
            status_code=401,
            detail="Root password not correct",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Create/Update 'api_user' with a random password
    api_pass = secrets.token_urlsafe(16)
    await create_mysql_user_if_not_exists(root, 'api_user', api_pass)
    os.environ["API_USER_PASS"] = api_pass

    # 3. Connect the “dataClient” and “userClient” with new creds
    dataClient = db()
    userClient = db()
    await dataClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'api_user',
        os.environ.get('API_USER_PASS'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )
    await userClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'api_user',
        os.environ.get('API_USER_PASS'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

# --------- Startup --------- #
@app.on_event("startup")
async def configure_db_and_routes():
    global dataClient
    global userClient
    os.environ["SETUP"] = "True"

    # 1. Attempt to connect using default root pass 
    rootClient = db()
    await rootClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'root',
        os.environ.get('ROOT_MONGO_PASSWORD'),  # we reuse same env var, though it's MySQL now
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

    # If fail, that means root pass is not correct => Setup is not done
    if not rootClient.passfail:
        os.environ["SETUP"] = "False"

    if os.environ["SETUP"] == "True":
        await rebuild_db_users(os.environ.get('ROOT_MONGO_PASSWORD'))

    dataClient = db()
    userClient = db()
    await dataClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'api_user',
        os.environ.get('API_USER_PASS'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )
    await userClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'api_user',
        os.environ.get('API_USER_PASS'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

# --------- Setup Logic --------- #
async def setup(root_password):
    """
    Update the MySQL root password if needed, then rebuild users with new pass.
    """
    # 1. Connect with old root password
    rootClient = db()
    await rootClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'root',
        os.environ.get('ROOT_MONGO_PASSWORD'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

    if not rootClient.passfail:
        print("Error: Failed to set root pass:")
        raise HTTPException(
            status_code=401,
            detail="ERROR: Default pass not working. Something went wrong",
        )

    # 2. Attempt to update root password
    try:
        rootClient.cursor.execute(f"ALTER USER 'root'@'%' IDENTIFIED BY '{root_password}';")
        rootClient.cursor.execute("FLUSH PRIVILEGES;")
        rootClient.connection.commit()
    except Exception as e:
        print("Error: Failed to update root password", e)
        raise HTTPException(
            status_code=500,
            detail="Error: Failed to update root password"
        )

    # 3. Attempt to reconnect with new root password to confirm
    oldRootClient = db()
    await oldRootClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'root',
        os.environ.get('ROOT_MONGO_PASSWORD'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )

    if oldRootClient.passfail:
        print("Error: old root password still works, maybe update fail")
        raise HTTPException(
            status_code=500,
            detail="Error: Failed to update root password"
        )
    else:
        os.environ["SETUP"] = "False"
        print("Database root pass change success!")

    # 4. Rebuild with new root pass
    await rebuild_db_users(root_password)
    return True

# --------- Basic CRUD for Users (MySQL) --------- #
def get_user(username: str):
    global userClient
    if not userClient.cursor:
        return None
    query = "SELECT * FROM users WHERE username = %s LIMIT 1"
    userClient.cursor.execute(query, (username,))
    row = userClient.cursor.fetchone()
    return row if row else None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

async def register(username, password, email):
    """
    Insert new user in MySQL if not existing; Return the user object or raise exception if conflict.
    """
    global userClient
    # Check for existing username or email
    query_check = "SELECT * FROM users WHERE username = %s OR email = %s LIMIT 1"
    userClient.cursor.execute(query_check, (username, email))
    existing = userClient.cursor.fetchone()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Insert user
    query_insert = """
        INSERT INTO users 
            (username, email, password_hash, disabled, roles, attributes, settings, joinDateTime)
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    roles = json.dumps([])         # store as JSON or comma-separated
    attributes = json.dumps(["weight","age","mood","journal"])
    settings = json.dumps([])

    userClient.cursor.execute(query_insert, (
        username,
        email,
        get_password_hash(password),
        False,
        roles,
        attributes,
        settings,
        datetime.now()
    ))
    userClient.connection.commit()

    # Return user from DB
    return authenticate_user(username, password)

# --------- Basic CRUD for Data (MySQL) --------- #
# Storing each 'attribute' in a table named data with JSON 'datapoints'
# You can adapt as needed.

async def createDataAttribute(attributeName, user):
    global dataClient
    query = """
        INSERT INTO data (username, attribute_name, next_document, datapoints, startTimeDate, endTimeDate)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    datapoints_json = json.dumps([])  # empty initial array
    dataClient.cursor.execute(query, (
        user['username'],
        attributeName,
        "",   # next_document
        datapoints_json,
        datetime.now(),
        datetime.now()
    ))
    dataClient.connection.commit()
    return dataClient.cursor.lastrowid

async def getDataArray(attributeName, user):
    global dataClient
    # Try to find data row(s) that match this user & attribute
    query = """SELECT * FROM data WHERE username = %s AND attribute_name = %s"""
    dataClient.cursor.execute(query, (user['username'], attributeName))
    rows = dataClient.cursor.fetchall()

    if not rows:
        return {"attr_name": attributeName, "data_array": []}

    # Sort by startTimeDate
    rows_sorted = sorted(rows, key=itemgetter('startTimeDate'))

    # Combine all datapoints (from each chunk) into one big list
    bigArr = []
    for row in rows_sorted:
        # row['datapoints'] is presumably JSON
        chunk = json.loads(row['datapoints']) if row['datapoints'] else []
        bigArr.extend(chunk)

    return {
        "attr_name": attributeName,
        "data_array": bigArr
    }

async def setDatapoint(attributeName, user, data):
    global dataClient

    # 1. Find the "latest" doc for that attribute
    query_find = """SELECT * FROM data 
                    WHERE username = %s AND attribute_name = %s
                    ORDER BY startTimeDate DESC
                    LIMIT 1
                 """
    dataClient.cursor.execute(query_find, (user['username'], attributeName))
    row = dataClient.cursor.fetchone()

    if not row:
        # create new attribute doc
        row_id = await createDataAttribute(attributeName, user)
        # retrieve it
        query_get = """SELECT * FROM data WHERE id = %s LIMIT 1"""
        dataClient.cursor.execute(query_get, (row_id,))
        row = dataClient.cursor.fetchone()

    # 2. Check if doc size is over 10MB (arbitrary check like in your code):
    #    We'll do a naive check by measuring the JSON size of 'row'
    #    In a real scenario, you might measure the DB column size, etc.
    row_json = json.dumps(row)
    if len(row_json.encode('utf-8')) > 10_000_000:
        # create new attribute doc, link the old doc's 'next_document'
        row_id = await createDataAttribute(attributeName, user)
        # update old doc
        query_update_old = """UPDATE data SET next_document = %s WHERE id = %s"""
        dataClient.cursor.execute(query_update_old, (row_id, row['id']))
        dataClient.connection.commit()
        # re-fetch the new row
        query_get_new = """SELECT * FROM data WHERE id = %s LIMIT 1"""
        dataClient.cursor.execute(query_get_new, (row_id,))
        row = dataClient.cursor.fetchone()

    # 3. Append new datapoint
    dp_list = json.loads(row['datapoints']) if row['datapoints'] else []
    dp_list.append({
        "timestamp": datetime.now().isoformat(),
        "data": data
    })

    # 4. Update that row in DB
    query_update = """
        UPDATE data
           SET datapoints = %s,
               endTimeDate = %s
         WHERE id = %s
    """
    dataClient.cursor.execute(query_update, (
        json.dumps(dp_list),
        datetime.now(),
        row['id']
    ))
    dataClient.connection.commit()

# --------- Security / Dependency --------- #
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    In the Mongo code, we tried connecting as root to see if DB was set up.
    We'll do a simpler check here:
    """
    # Check if root password doesn't connect => Then passfail is false => Not setup
    rootClient = db()
    await rootClient.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'root',
        os.environ.get('ROOT_MONGO_PASSWORD'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )
    if rootClient.passfail:
        # If we actually can connect, that implies setup not finished in your original logic
        raise notSetupError

    # Also ensure dataClient is valid
    dataClient_test = db()
    await dataClient_test.connect(
        os.environ.get('MYSQL_DATABASE', 'admin'),
        'api_user',
        os.environ.get('API_USER_PASS'),
        host=os.environ.get('MYSQL_HOST', 'db'),
        port=int(os.environ.get('MYSQL_PORT', '3306'))
    )
    if not dataClient_test.passfail:
        print("App needs rebuild:")
        raise HTTPException(
            status_code=398,
            detail="App needs to be rebuilt",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Normal JWT decode
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

# --------- API Endpoints --------- #
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
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=Union[Token, ErrorResponse])
async def register_and_get_token(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    email: Annotated[str, Form()]
):
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
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=Union[User, ErrorResponse])
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@app.post("/setup/setRoot")
async def set_root_password(password: str = Form(...)):
    if os.environ["SETUP"] != "True":
        raise HTTPException(
            status_code=400,
            detail="App already set up"
        )
    await setup(password)

@app.post("/setup/rebuild")
async def rebuild(password: str = Form(...)):
    await rebuild_db_users(password)

@app.get("/get/{attrName}", response_model=Union[DataArray, ErrorResponse])
async def getData(attrName, current_user: Annotated[User, Depends(get_current_active_user)]):
    dataArr = await getDataArray(attrName, current_user)
    return dataArr

@app.get("/getMany", response_model=Union[Dict[str, List[DataArray]], ErrorResponse])
async def getMuchData(
    current_user: Annotated[User, Depends(get_current_active_user)],
    a: Annotated[List[str], Query()] = []
):
    result = []
    if a:
        for attr in a:
            result.append(await getDataArray(attr, current_user))
    return {"data": result}

@app.post("/set")
async def setData(
    attribute_name: Annotated[str, Form()],
    datapoint: Annotated[Any, Form()],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    await setDatapoint(attribute_name, current_user, datapoint)

@app.get("/test")
async def setData():
    return {"data": "TEST"}
