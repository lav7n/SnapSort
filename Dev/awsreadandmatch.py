from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cv2
import numpy as np
from io import BytesIO
from scipy.spatial.distance import cosine
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from uuid import uuid4
from pymongo import MongoClient
from ultralytics import YOLO
from deepface.DeepFace import represent
import base64
import io
import random
import string
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os
import faiss
import requests
import os
import json
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"



# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient("mongodb+srv://anirvesh:anirvesh@cluster0.tuw5ikl.mongodb.net")
db = client["snap-sort"]

feature_vector_collection = db["image_feature_vectors"]
users_collection = db["users"]
events_collection = db["events"]


faiss_indices = {}
dimension = 4096

# Constants
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CDN_BASE_URL = "https://your-cdn.com/"
CDN_UPLOAD_URL = "https://your-cdn.com/upload"
# YOLO model
model = YOLO("model.pt")

# Pydantic models
class FaceMatchingRequest(BaseModel):
    similarity_threshold: float

class ImageData(BaseModel):
    base64_images: List[str]

class RegisterUser(BaseModel):
    name: str
    email: str
    password: str
    image: str

class LoginRequest(BaseModel):
    email: str
    password: str

class User(BaseModel):
    email: str
    name: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

# Helper functions

def fetch_image_from_cdn(image_url):
    """Fetch image from the CDN and return it as a NumPy array."""
    response = requests.get(image_url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {image_url}")
    
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {image_url}")
    
    return image


def upload_to_cdn(file_name, json_data):
    """Uploads JSON file to the CDN."""
    files = {"file": (file_name, json.dumps(json_data), "application/json")}
    response = requests.post(CDN_UPLOAD_URL, files=files)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to upload matches.json to CDN")

    return response.json().get("url")  # Assuming CDN returns the file URL


def localize_faces_func(image):
    results = model.predict(source=image, conf=0.25)
    face_boxes = []
    for box in results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, box)
        face_boxes.append((x1, y1, x2, y2))
    return face_boxes

def extract_features_func(face_image):
    result = represent(face_image, model_name="VGG-Face", enforce_detection=False, align=True)
    return result[0]["embedding"]


def normalize_vectors(vectors):
    """Normalize vectors to unit length for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1)
    normalized_vectors = vectors / np.maximum(norms[:, np.newaxis], 1e-10)
    return normalized_vectors.astype('float32')

def process_image(file,event_id, similarity_threshold):
    # file = {image,file_key}
    try:
        image = file["image"]
        if image is None:
            print(f"Failed to read image: {file}")
            return None

        bounding_boxes = localize_faces_func(image)
        image_matches = {}
        
        # Get all feature vectors and their IDs from MongoDB
        all_records = list(feature_vector_collection.find())
        
        for box in bounding_boxes:
            x, y, w, h = box
            face_image = image[y:y+h, x:x+w]
            query_vector = np.array(extract_features_func(face_image))
            normalized_query = normalize_vectors(query_vector.reshape(1, -1))
            
            k = 1 
            similarities, indices = faiss_indices[event_id].search(normalized_query, k)
            
            # Process results
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= similarity_threshold:
                    person_id = all_records[idx]["id"]
                    if person_id not in image_matches:
                        image_matches[person_id] = []
                    image_matches[person_id].append({
                        "file_key": file["file_key"],
                        "bounding_box": box,
                        "similarity": float(sim)
                    })
        
        return image_matches

    except Exception as e:
        print(f"Error processing image : {e}")
        return None

@app.post("/process_user_images/{event_id}")
async def process_user_images(event_id: str):
    stored_data = []
    try:
        event = events_collection.find_one({"_id": event_id}, {"participants": 1})
        if not event or "participants" not in event:
            raise HTTPException(status_code=400, detail="Event not found or has no participants")
        
        user_ids = event["participants"]
        user_records = list(users_collection.find({"id": {"$in": user_ids}}, {"_id": 0, "image": 1, "id": 1}))
        if not user_records:
            raise HTTPException(status_code=400, detail="No user images found")
        
        all_records = list(feature_vector_collection.find({"id": {"$in": user_ids}}, {"_id": 0, "feature_vector": 1, "id": 1}))
        existing_ids = {record["id"] for record in all_records}
        
        new_vectors = []
        new_records = []
        
        for user in user_records:
            id = user["id"]
            if id in existing_ids:
                continue

            image = user["image"]
            if image is None:
                raise ValueError(f"Invalid image data for user ID {id}")
            
            box = localize_faces_func(image)
            x, y, w, h = box[0]
            face_image = image[y:y+h, x:x+w]
            feature_vector = extract_features_func(face_image)
            
            record = {"feature_vector": np.array(feature_vector).tolist(), "id": id}
            feature_vector_collection.update_one(
                {"id": id},
                {"$set": record},
                upsert=True
            )
            
            new_vectors.append(feature_vector)
            new_records.append(record)
            stored_data.append(record)
        
        if new_vectors:
            if event_id not in faiss_indices:
                faiss_indices[event_id] = faiss.IndexFlatIP(dimension)  # Initialize FAISS index if not present
            
            index = faiss_indices[event_id]
            new_vectors_array = np.array(new_vectors)
            normalized_vectors = normalize_vectors(new_vectors_array)
            index.add(normalized_vectors)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing user images: {str(e)}")
    
    return {"message": "User images processed and data stored successfully", "stored_data": stored_data}

@app.post("/match_faces/{event_id}")
async def match_faces(event_id: str,request: FaceMatchingRequest):
    """Match faces from stored images for a specific event from CDN."""
    try:
        # Construct CDN directory URL
        event_directory_url = f"{CDN_BASE_URL}{event_id}/"

        # Fetch image file list from CDN (Assuming a JSON API returns file names)
        response = requests.get(event_directory_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Event images directory not found on CDN")
        
        image_files = response.json().get("images", [])  # Assuming CDN API returns {"images": ["image1.jpg", "image2.png"]}

        matches = {}

        for file_name in image_files:
            image_url = f"{event_directory_url}{file_name}"
            image = fetch_image_from_cdn(image_url)

            file = {"image": image, "file_key": file_name}
            result = process_image(file, event_id, request.similarity_threshold)

            if result:
                for person_id, file_matches in result.items():
                    if person_id not in matches:
                        matches[person_id] = []
                    matches[person_id].extend([match['file_path'] for match in file_matches])
                

        matches_json = {"matches": matches}
        matches_json_url = upload_to_cdn(f"{request.event_id}/matches.json", matches_json)

        return {
            "message": "Face matching completed successfully",
            "matches_file_url": matches_json_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    
@app.post("/register")
def register_user(user: RegisterUser):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered for this event.")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid4())
    user_data = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hashed_password.decode('utf-8'),
        "image": user.image,
        "event_ids": []
    }
    users_collection.insert_one(user_data)
    return {"id": user_id, "name": user.name, "email": user.email}

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = users_collection.find_one({"email": request.email})
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not bcrypt.checkpw(request.password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": user["email"]})
    user_response = User(email=user["email"], name=user.get("name", ""))
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


def generate_event_code():
    return "-".join("".join(random.choices(string.ascii_lowercase + string.digits, k=4)) for _ in range(3))




