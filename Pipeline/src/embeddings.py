from deepface import DeepFace
from tqdm import tqdm
import numpy as np
import os

def ExtractEmbeddings(faces_folder, model_name="VGG-Face"):
    embeds, img_map = [], []
    for img in tqdm(os.listdir(faces_folder), desc="Extracting Embeddings"):
        try:
            rep = DeepFace.represent(os.path.join(faces_folder, img), model_name=model_name, enforce_detection=False)
            if rep:
                embeds.append(rep[0]["embedding"])
                img_map.append(img)
        except: continue
    return np.array(embeds, dtype="float32"), img_map