import numpy as np
from sklearn.neighbors import NearestNeighbors

# Perform K-nearest neighbors (KNN) search
def knn_search(question_embedding, embeddings, k=5):
    X = np.array([item['embedding'] for article in embeddings for item in article['embeddings']])
    source_texts = [item['source'] for article in embeddings for item in article['embeddings']]
    k = min(k, len(source_texts))
    
    # Fit a KNN model on the embeddings
    knn = NearestNeighbors(n_neighbors=k, metric='cosine')
    knn.fit(X)
    
    # Find the indices and distances of the k-nearest neighbors
    distances, indices = knn.kneighbors(question_embedding, n_neighbors=k)
    
    # Get the indices and source texts of the best matches
    best_matches = [(indices[0][i], source_texts[indices[0][i]]) for i in range(k)]
    
    return best_matches