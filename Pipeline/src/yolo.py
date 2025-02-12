# yolo.py
import os
import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

def DetectFaces(input_folder, output_folder="detected_faces", model_path="model.pt", conf_threshold=0.25):
    os.makedirs(output_folder, exist_ok=True)
    image_results = {}
    yolo_model = YOLO(model_path)
    valid_images = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
    
    for filename in tqdm(valid_images, desc="Detecting Faces"):
        image = cv2.imread(os.path.join(input_folder, filename))
        if image is None: continue
        results = yolo_model.predict(source=image, conf=conf_threshold, verbose=False)
        face_boxes = []
        
        for i, box in enumerate(results[0].boxes.xyxy, 1):
            x1, y1, x2, y2 = map(int, box)
            cv2.imwrite(os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_face_{i}.jpg"), 
                        image[y1:y2, x1:x2])
            face_boxes.append((x1, y1, x2, y2))
        image_results[filename] = face_boxes
    return image_results, output_folder