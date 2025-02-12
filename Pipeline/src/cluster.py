from sklearn.cluster import KMeans
from collections import defaultdict

def ClusterFaces(embeddings, img_map, n_clusters=5):
    if len(embeddings) == 0: return {}
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embeddings)
    clusters = defaultdict(list)
    for img, label in zip(img_map, labels):
        clusters[label].append(img)
    return clusters