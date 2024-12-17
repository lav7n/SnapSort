from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError
import cv2
import numpy as np
from io import BytesIO
from scipy.spatial.distance import cosine
from concurrent.futures import ThreadPoolExecutor
from typing import List
from uuid import uuid4
from pymongo import MongoClient
from ultralytics import YOLO
from deepface.DeepFace import represent
import base64
import io
from sklearn.cluster import MiniBatchKMeans



kmeans = MiniBatchKMeans(n_clusters=3, random_state=42, batch_size=100)
app = FastAPI()
client = MongoClient("mongodb+srv://anirvesh:anirvesh@cluster0.tuw5ikl.mongodb.net")
db = client["image_database"]
feature_vector_collection = db["image_feature_vectors"]
cluster_means_collection = db["cluster_means"]


model = YOLO("model.pt")

class FaceMatchingRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    region: str
    s3_url: str
    similarity_threshold: float

class ImageData(BaseModel):
    base64_images: List[str]

def localize_faces_func(image):
    results = model.predict(source=image, conf=0.25)
    face_boxes = []
    for box in results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, box)
        face_boxes.append((x1, y1, x2, y2))
    return face_boxes

def extract_features_func(face_image):
    result = represent(face_image, model_name="VGG-Face", enforce_detection=False,align=True)
    return(result[0])


def process_image(file_key, s3_client, bucket_name, feature_dict, similarity_threshold):
    try:
        clusters=cluster_means_collection.find()
        file_object = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = file_object['Body'].read()
        image = cv2.imdecode(np.frombuffer(file_content, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            print(f"Failed to decode image: {file_key}")
            return None
        bounding_boxes = localize_faces_func(image)
        image_matches = {}
        for box in bounding_boxes:
            x, y, w, h = box
            face_image = image[y:y+h, x:x+w]
            face_vector = extract_features_func(face_image)
            closest_cluster = None
            min_distance = float('inf')
            for cluster in clusters:
                mean_vector = cluster["mean_feature_vector"]
                distance = np.linalg.norm(np.array(face_vector) - np.array(mean_vector))
                if distance < min_distance:
                    min_distance = distance
                    closest_cluster = cluster["cluster"]
            for known_vector, (person_id, cluster_id) in feature_dict.items():
                if cluster_id == closest_cluster:
                    similarity = 1 - cosine(face_vector, known_vector)
                    if similarity >= similarity_threshold:
                        if person_id not in image_matches:
                            image_matches[person_id] = []
                        image_matches[person_id].append({
                            "file_key": file_key,
                            "bounding_box": box,
                            "similarity": similarity,
                            "cluster": closest_cluster
                        })
        return image_matches

    except Exception as e:
        print(f"Error processing image {file_key}: {e}")
        return None

@app.post("/match_faces")
async def match_faces(request: FaceMatchingRequest):
    try:
        feature_vector_collection_as_dict={}
        for document in feature_vector_collection.find():
            feature_vector = tuple(document["feature_vector"])
            unique_id = document["unique_id"]
            cluster_number = document["cluster"]
            feature_vector_collection_as_dict[feature_vector] = {unique_id, cluster_number}

        s3_url = request.s3_url
        bucket_name = s3_url.split('/')[2]
        prefix = '/'.join(s3_url.split('/')[3:])
        s3_client = boto3.client(
            's3',
            aws_access_key_id=request.aws_access_key,
            aws_secret_access_key=request.aws_secret_key,
            region_name=request.region
        )
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' not in response:
            raise HTTPException(status_code=404, detail="No files found in the specified S3 path.")
        image_files = [
            obj['Key'] for obj in response['Contents']
            if obj['Key'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ]
        matches = {}
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    process_image, file_key, s3_client, bucket_name,
                    feature_vector_collection_as_dict, request.similarity_threshold
                )
                for file_key in image_files
            ]
            for future in futures:
                result = future.result()
                if result:
                    for person_id, file_keys in result.items():
                        if person_id not in matches:
                            matches[person_id] = []
                        matches[person_id].extend(file_keys)

        return {"matches": matches}

    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")




@app.post("/upload_images")
async def upload_images(data: ImageData):
    if not data.base64_images:
        raise HTTPException(status_code=400, detail="No images provided")
    stored_data = []

    try:
        all_records = list(feature_vector_collection.find({}, {"_id": 0, "feature_vector": 1, "unique_id": 1}))
        feature_vectors = [record["feature_vector"] for record in all_records]
        unique_ids = [record["unique_id"] for record in all_records]

        new_feature_vectors = []
        for base64_str in data.base64_images:
            image_data = base64.b64decode(base64_str)
            np_image = np.frombuffer(image_data, dtype=np.uint8)
            image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Invalid image data")
            feature_vector = extract_features_func(image).tolist()
            new_feature_vectors.append(feature_vector)

            unique_id = str(uuid4())
            unique_ids.append(unique_id)
            record = {"feature_vector": feature_vector, "unique_id": unique_id}
            stored_data.append(record)
        feature_vectors.extend(new_feature_vectors)
        kmeans.partial_fit(feature_vectors)
        cluster_labels = kmeans.predict(feature_vectors)

        for i, unique_id in enumerate(unique_ids):
            feature_vector_collection.update_one(
                {"unique_id": unique_id},
                {"$set": {"cluster": int(cluster_labels[i])}},
                upsert=True
            )

        for record, cluster_label in zip(stored_data, cluster_labels[-len(new_feature_vectors):]):
            record["cluster"] = int(cluster_label)
        cluster_vectors = {i: [] for i in range(kmeans.n_clusters)}
        for vector, label in zip(feature_vectors, cluster_labels):
            cluster_vectors[label].append(vector)

        mean_vectors = {}
        for cluster, vectors in cluster_vectors.items():
            if vectors:
                mean_vector = np.mean(vectors, axis=0).tolist()
                mean_vectors[cluster] = mean_vector
                cluster_means_collection.update_one(
                    {"cluster": cluster},
                    {"$set": {"mean_feature_vector": mean_vector}},
                    upsert=True
                )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")

    return {
        "message": "Images processed, clustered, and data stored successfully",
        "stored_data": stored_data
    }
