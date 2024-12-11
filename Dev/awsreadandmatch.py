from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError
import cv2
import numpy as np
from io import BytesIO
from scipy.spatial.distance import cosine
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

class FaceMatchingRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    region: str
    s3_url: str
    similarity_threshold: float
    feature_dict: dict


def localize_faces_func(image):
    return [(50, 50, 100, 100)]

def extract_features_func(face_image):
    return np.random.rand(128)


def process_image(file_key, s3_client, bucket_name, feature_dict, similarity_threshold):
    try:
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
            for known_vector, person_id in feature_dict.items():
                similarity = 1 - cosine(face_vector, known_vector)
                if similarity >= similarity_threshold:
                    if person_id not in image_matches:
                        image_matches[person_id] = []
                    image_matches[person_id].append(file_key)

        return image_matches

    except Exception as e:
        print(f"Error processing image {file_key}: {e}")
        return None

@app.post("/match_faces")
async def match_faces(request: FaceMatchingRequest):
    try:
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
                    request.feature_dict, request.similarity_threshold
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
