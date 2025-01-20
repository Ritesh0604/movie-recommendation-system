import os
from database import initialize_database, load_data_from_db
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, '..', 'data', 'movie_recommendation.db')

    # Remove the existing database file if it exists
    if os.path.exists(db_path):
        logger.info(f"Removing existing database file: {db_path}")
        os.remove(db_path)

    logger.info("Starting database initialization...")
    initialize_database()
    logger.info("Database initialization complete.")

    logger.info("Attempting to load data from the database...")
    try:
        movies, ratings, tags, links = load_data_from_db()
        logger.info(f"Successfully loaded {len(movies)} movies, {len(ratings)} ratings, and {len(tags)} tags.")
    except Exception as e:
        logger.error(f"Error loading data from database: {e}")
