# main.py
import os
from src.yolo import DetectFaces
from src.embeddings import ExtractEmbeddings
from src.cluster import ClusterFaces
from src.test import EvaluateMatches, PrintEvaluationReport, FindSimilarFaces

def RunPipeline(input_folder):
    results, faces_folder = DetectFaces(input_folder)
    embeddings, img_map = ExtractEmbeddings(faces_folder)
    clusters = ClusterFaces(embeddings, img_map)
    groups = FindSimilarFaces(embeddings, img_map)
    metrics = EvaluateMatches(groups)
    PrintEvaluationReport(metrics)

if __name__ == "__main__":
    input_folder = "input_images"  # Change as needed
    RunPipeline(input_folder)
