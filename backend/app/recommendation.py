import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack
import os
import logging
from functools import lru_cache
from .database import load_data_from_db
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load and preprocess data
@lru_cache(maxsize=1)
def load_data():
    logger.info("Loading data from database...")
    movies, ratings, tags= load_data_from_db()

    logger.info(f"Loaded {len(movies)} movies, {len(ratings)} ratings, {len(tags)} tags")

    # Ensure data types are correct
    ratings['movieId'] = ratings['movieId'].astype(int)
    ratings['userId'] = ratings['userId'].astype(int)

    # Combine genres and tags for each movie
    movies['genres'] = movies['genres'].fillna('')
    tags['tag'] = tags['tag'].astype(str).replace('nan', '')
    tags_grouped = tags.groupby('movieId')['tag'].apply(' '.join).reset_index()
    
    # Merge tags with movie data
    movies = movies.merge(tags_grouped, on='movieId', how='left')
    movies['tags'] = movies['tag'].fillna('')

    logger.info("Data loading and preprocessing complete.")
    return movies, ratings

def create_latent_matrix(ratings, movies):
    # Create a pivot table with all movies, filling missing values with 0
    all_movie_ids = movies['movieId'].unique()
    all_user_ids = ratings['userId'].unique()
    
    ratings_matrix = pd.pivot_table(ratings, values='rating', index='userId', columns='movieId', fill_value=0)
    
    # Add missing movies as columns with zero ratings
    missing_movies = set(all_movie_ids) - set(ratings_matrix.columns)
    for movie_id in missing_movies:
        ratings_matrix[movie_id] = 0
    
    # Ensure all users are included
    missing_users = set(all_user_ids) - set(ratings_matrix.index)
    for user_id in missing_users:
        ratings_matrix.loc[user_id] = 0
    
    # Sort columns to ensure consistent order
    ratings_matrix = ratings_matrix.sort_index(axis=1)
    
    logger.info(f"Ratings matrix shape: {ratings_matrix.shape}")

    # Standardize the ratings
    scaler = StandardScaler()
    ratings_scaled = scaler.fit_transform(ratings_matrix)

    # Perform SVD
    svd = TruncatedSVD(n_components=50)  # Choose the number of components
    latent_matrix = svd.fit_transform(ratings_scaled)

    return ratings_matrix, latent_matrix

# Load data
movies, ratings = load_data()
ratings_matrix, latent_matrix = create_latent_matrix(ratings, movies)

# TF-IDF Vectorizer for genres and tags separately
def create_tfidf_matrix(movies):
    genre_tfidf = TfidfVectorizer(stop_words='english')
    tag_tfidf = TfidfVectorizer(stop_words='english')

    genre_matrix = genre_tfidf.fit_transform(movies['genres'])
    tag_matrix = tag_tfidf.fit_transform(movies['tags'])

    logger.info(f"Created TF-IDF matrix for genres: {genre_matrix.shape}, and tags: {tag_matrix.shape}")
    
    # Combine the two matrices using scipy's sparse hstack
    combined_matrix = hstack([genre_matrix, tag_matrix])
    return combined_matrix

# Create the combined TF-IDF matrix
tfidf_matrix = create_tfidf_matrix(movies)

# Find exact matching movie titles
def find_similar_titles(input_title):
    input_title = input_title.lower()
    similar_titles = []
    
    for title in movies['title']:
        title_without_year = ' '.join(title.split()[:-1]).lower()
        if input_title in title_without_year:
            similar_titles.append(title)
    
    return similar_titles

# Collaborative filtering using Matrix Factorization (SVD)
def collaborative_filtering(movie_id, movie_ids, latent_matrix, ratings_matrix, n=5):
    if isinstance(movie_id, int):
        movie_id = [movie_id]

    recommendations = []
    for mid in movie_id:
        if mid in ratings_matrix.columns:
            movie_index = ratings_matrix.columns.get_loc(mid)
            if movie_index < latent_matrix.shape[1]:
                movie_vector = latent_matrix[:, movie_index]
                similarities = np.dot(latent_matrix.T, movie_vector)
                similar_indices = similarities.argsort()[::-1][1:n + 1]
                similar_movie_ids = [ratings_matrix.columns[i] for i in similar_indices]
                recommendations.extend(similar_movie_ids)
            # else:
            #     logger.warning(f"Movie index {movie_index} out of bounds for the latent matrix")
        else:
            logger.warning(f"Movie ID {mid} not found in ratings matrix")

    return recommendations

# Combine content-based and collaborative filtering recommendations
def get_movie_recommendations(input_movies, n=5):
    logger.info(f"Received input movies: {input_movies}")
    
    # Load datasets and create movie_ids
    # movies, ratings = load_data()
    movie_ids = movies['movieId'].tolist()
    
    # # Create latent matrix
    # ratings_matrix, latent_matrix = create_latent_matrix(ratings, movies)

    # Step 1: Content-based filtering
    all_similar_titles = []
    for movie in input_movies:
        similar_titles = find_similar_titles(movie)
        all_similar_titles.extend(similar_titles)
    
    logger.info(f"Found similar titles: {all_similar_titles}")
    
    # Find movie IDs for similar titles
    input_ids = movies[movies['title'].isin(all_similar_titles)]['movieId'].tolist()
    
    if not input_ids:
        logger.warning("No matching movies found in the database")
        return []
    
    # Get the feature vectors for input movies
    input_vectors = tfidf_matrix[movies.index[movies['movieId'].isin(input_ids)]]
    
    # Calculate similarity scores for content-based recommendations
    sim_scores = cosine_similarity(input_vectors, tfidf_matrix).mean(axis=0)
    top_indices = sim_scores.argsort()[-n-len(input_ids):][::-1]
    
    # Get top content-based recommendations
    content_recommendations = [movies.iloc[i]['title'] for i in top_indices if movies.iloc[i]['movieId'] not in input_ids]
    
    logger.info(f"Content-based recommendations: {content_recommendations}")
    
    # Step 2: Collaborative filtering
    collaborative_recommendations = []
    for movie_id in input_ids:
        collaborative_recommendations.extend(collaborative_filtering(movie_id, movie_ids, latent_matrix, ratings_matrix, n=n))
    
    logger.info(f"Collaborative filtering recommendations: {collaborative_recommendations}")
    
    # Combine and return unique recommendations
    combined_recommendations = list(set(content_recommendations + collaborative_recommendations))
    
    return combined_recommendations[:n]
