from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
import secrets
import string
from fastapi import UploadFile, File
import requests

app = FastAPI()

CDN_UPLOAD_URL = "https://your-cdn-endpoint.com/upload"
client = MongoClient("mongodb://localhost:27017")
db = client["event_management"]
admins_collection = db["admins"]
events_collection = db["events"]
moderators_collection = db["moderators"]


SUPERADMIN_USERNAME = "superadmin"
SUPERADMIN_PASSWORD = "SuperSecret123" 


SECRET_KEY = "your_jwt_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/superadmin/login/")
async def login_superadmin(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != SUPERADMIN_USERNAME or form_data.password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": SUPERADMIN_USERNAME, "role": "superadmin"})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/admin/login/")
async def login_admin(form_data: OAuth2PasswordRequestForm = Depends()):
    admin = admins_collection.find_one({"username": form_data.username, "password": form_data.password})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    token = create_access_token({"sub": form_data.username, "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}


async def verify_superadmin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "superadmin":
            raise HTTPException(status_code=403, detail="Only Superadmin can access this route")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only Admins can access this route")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))


@app.post("/superadmin/create_admin/")
async def create_admin(username: str, token: dict = Depends(verify_superadmin)):
    if admins_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Admin with this username already exists")

    password = generate_password()
    admin_data = {"username": username, "password": password}
    result = admins_collection.insert_one(admin_data)

    return {"message": "Admin created successfully", "admin_id": str(result.inserted_id), "password": password}


@app.get("/superadmin/list_admins/")
async def list_admins(token: dict = Depends(verify_superadmin)):
    admins = list(admins_collection.find({}, {"_id": 1, "username": 1, "password": 1}))
    for admin in admins:
        admin["_id"] = str(admin["_id"])
    
    return {"admins": admins}

@app.delete("/superadmin/delete_admin/{username}")
async def delete_admin(username: str, token: dict = Depends(verify_superadmin)):
    result = admins_collection.delete_one({"username": username})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")

    return {"message": f"Admin '{username}' deleted successfully"}

@app.post("/admin/create_event/")
async def create_event(event_name: str, description: str, token: dict = Depends(verify_admin)):
    event_data = {"event_name": event_name, "description": description, "created_at": datetime.utcnow() , "moderators":[]}
    result = events_collection.insert_one(event_data)

    return {"message": "Event created successfully", "event_id": str(result.inserted_id)}


@app.post("/admin/create_moderator/")
async def create_moderator(event_id: str, name: str, token: dict = Depends(verify_admin)):
    event = events_collection.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    password = generate_password()
    moderator_data = {"name": name, "password": password, "event_id": event_id}
    
    events_collection.update_one({"_id": event_id}, {"$push": {"moderators": moderator_data}})
    moderators_collection.insert_one(moderator_data)
    
    return {"message": "Moderator created successfully", "event_id": event_id, "moderator_name": name, "password": password}

@app.post("/moderator/login/")
async def login_moderator(form_data: OAuth2PasswordRequestForm = Depends()):
    moderator = moderators_collection.find_one({"name": form_data.username, "password": form_data.password})
    if not moderator:
        raise HTTPException(status_code=401, detail="Invalid moderator credentials")
    
    token = create_access_token({"sub": form_data.username, "role": "moderator"})
    return {"access_token": token, "token_type": "bearer"}

def verify_moderator(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "moderator":
            raise HTTPException(status_code=403, detail="Only Moderators can access this route")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

@app.post("/moderator/upload_file/")
async def upload_file(event_id: str, file: UploadFile = File(...), token: dict = Depends(verify_moderator)):
    """Allows moderators to upload files to the CDN under their assigned event directory."""
    files = {"file": (file.filename, await file.read(), file.content_type)}
    upload_url = f"{CDN_UPLOAD_URL}/{event_id}/"
    response = requests.post(upload_url, files=files)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to upload file to CDN")
    
    return {"message": "File uploaded successfully", "file_url": response.json().get("url")}

    