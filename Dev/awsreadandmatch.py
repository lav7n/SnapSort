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
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import os
import faiss
import os
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

# Constants
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# YOLO model
model = YOLO("model.pt")

# Pydantic models
class FaceMatchingRequest(BaseModel):
    local_directory: str
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




dimension = 4096
index = faiss.IndexFlatIP(dimension)

def normalize_vectors(vectors):
    """Normalize vectors to unit length for cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1)
    normalized_vectors = vectors / np.maximum(norms[:, np.newaxis], 1e-10)
    return normalized_vectors.astype('float32')

def initialize_faiss_index():
    """Initialize FAISS index with existing vectors from MongoDB."""
    global index
    
    # Fetch all feature vectors from MongoDB
    all_records = list(feature_vector_collection.find({}, {"feature_vector": 1}))
    if not all_records:
        return
    
    # Convert to numpy array and normalize
    vectors = np.array([record["feature_vector"] for record in all_records])
    normalized_vectors = normalize_vectors(vectors)
    
    # Reset and rebuild index
    index = faiss.IndexFlatIP(dimension)
    index.add(normalized_vectors)

@app.on_event("startup")
async def startup_event():
    """Initialize FAISS index when the application starts."""
    initialize_faiss_index()

def process_image(file_key, similarity_threshold):
    try:
        image = cv2.imread(file_key)
        if image is None:
            print(f"Failed to read image: {file_key}")
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
            similarities, indices = index.search(normalized_query, k)
            
            # Process results
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= similarity_threshold:
                    person_id = all_records[idx]["unique_id"]
                    if person_id not in image_matches:
                        image_matches[person_id] = []
                    image_matches[person_id].append({
                        "file_key": file_key,
                        "bounding_box": box,
                        "similarity": float(sim)
                    })
        
        return image_matches

    except Exception as e:
        print(f"Error processing image {file_key}: {e}")
        return None

@app.post("/process_user_images")
async def process_user_images():
    stored_data = []

    try:
        user_records = list(users_collection.find({}, {"_id": 0, "image": 1, "id": 1}))
        if not user_records:
            raise HTTPException(status_code=400, detail="No users or images found")

        # Get existing feature vectors and IDs
        all_records = list(feature_vector_collection.find({}, {"_id": 0, "feature_vector": 1, "unique_id": 1}))
        existing_ids = {record["unique_id"] for record in all_records}
        
        new_vectors = []
        new_records = []
        
        for user in user_records:
            unique_id = user["id"]
            if unique_id in existing_ids:
                continue

            # Process image and extract features
            base64_str = user["image"]
            if base64_str.startswith("data:image/"):
                base64_str = base64_str.split(",")[1]
            image_data = base64.b64decode(base64_str)
            np_image = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Invalid image data for user ID {unique_id}")

            box = localize_faces_func(image)
            x, y, w, h = box[0]
            face_image = image[y:y+h, x:x+w]
            feature_vector = extract_features_func(face_image)
            
            # Store in MongoDB
            record = {"feature_vector": np.array(feature_vector).tolist(), "unique_id": unique_id}
            feature_vector_collection.update_one(
                {"unique_id": unique_id},
                {"$set": record},
                upsert=True
            )
            
            # Collect for FAISS update
            new_vectors.append(feature_vector)
            new_records.append(record)
            stored_data.append(record)

        if new_vectors:
            # Update FAISS index with new vectors
            new_vectors_array = np.array(new_vectors)
            normalized_vectors = normalize_vectors(new_vectors_array)
            index.add(normalized_vectors)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing user images: {str(e)}")

    return {
        "message": "User images processed and data stored successfully",
        "stored_data": stored_data
    }

@app.post("/match_faces")
async def match_faces(request: FaceMatchingRequest):
    try:
        local_directory_path = "queue"
        image_files = [
            os.path.join(local_directory_path, file)
            for file in os.listdir(local_directory_path)
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ]

        matches = {}
        for file_path in image_files:
            result = process_image(file_path, request.similarity_threshold)
            if result:
                for person_id, file_matches in result.items():
                    if person_id not in matches:
                        matches[person_id] = []
                    matches[person_id].extend([match['file_key'] for match in file_matches])

        return {"matches": matches}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
@app.post("/register")
def register_user(user: RegisterUser):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid4())
    user_data = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hashed_password.decode('utf-8'),
        "image": user.image,
    }
    result = users_collection.insert_one(user_data)
    return {
        "id": user_id,
        "name": user.name,
        "email": user.email,
    }

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