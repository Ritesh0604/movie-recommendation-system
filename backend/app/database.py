import sqlite3
import pandas as pd
import os
from sqlalchemy import create_engine
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, '..', 'data', 'movie_recommendation.db')

def create_connection():
    try:
        conn = sqlite3.connect(db_path)
        logger.debug(f"Successfully connected to database at {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS movies")
        cursor.execute("DROP TABLE IF EXISTS ratings")
        cursor.execute("DROP TABLE IF EXISTS tags")
        
        cursor.execute('''
        CREATE TABLE movies (
            movieId INTEGER PRIMARY KEY,
            title TEXT,
            genres TEXT
        )
        ''')
        logger.debug("Created movies table")

        cursor.execute('''
        CREATE TABLE ratings (
            userId INTEGER,
            movieId INTEGER,
            rating REAL,
            timestamp INTEGER,
            FOREIGN KEY (movieId) REFERENCES movies (movieId)
        )
        ''')
        logger.debug("Created ratings table")

        cursor.execute('''
        CREATE TABLE tags (
            userId INTEGER,
            movieId INTEGER,
            tag TEXT,
            timestamp INTEGER,
            FOREIGN KEY (movieId) REFERENCES movies (movieId)
        )
        ''')
        logger.debug("Created tags table")

        conn.commit()
        logger.info("All tables created successfully")
    except sqlite3.Error as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def import_csv_to_sqlite():
    create_tables()
    
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Import movies
        movies_csv_path = os.path.join(current_dir, '..', 'data', 'movies.csv')
        if os.path.exists(movies_csv_path):
            movies_df = pd.read_csv(movies_csv_path)
            movies_df.to_sql('movies', engine, if_exists='replace', index=False)
            logger.info(f"Imported {len(movies_df)} movies")
        else:
            logger.error(f"Movies CSV file not found at {movies_csv_path}")

        # Import ratings
        ratings_csv_path = os.path.join(current_dir, '..', 'data', 'ratings.csv')
        if os.path.exists(ratings_csv_path):
            ratings_df = pd.read_csv(ratings_csv_path)
            ratings_df.to_sql('ratings', engine, if_exists='replace', index=False)
            logger.info(f"Imported {len(ratings_df)} ratings")
        else:
            logger.error(f"Ratings CSV file not found at {ratings_csv_path}")

        # Import tags
        tags_csv_path = os.path.join(current_dir, '..', 'data', 'tags.csv')
        if os.path.exists(tags_csv_path):
            tags_df = pd.read_csv(tags_csv_path)
            tags_df.to_sql('tags', engine, if_exists='replace', index=False)
            logger.info(f"Imported {len(tags_df)} tags")
        else:
            logger.error(f"Tags CSV file not found at {tags_csv_path}")
            
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise

def load_data_from_db():
    conn = create_connection()
    
    try:
        movies = pd.read_sql_query("SELECT * FROM movies", conn)
        logger.info(f"Loaded {len(movies)} movies from database")
        ratings = pd.read_sql_query("SELECT * FROM ratings", conn)
        logger.info(f"Loaded {len(ratings)} ratings from database")
        tags = pd.read_sql_query("SELECT * FROM tags", conn)
        logger.info(f"Loaded {len(tags)} tags from database")
    except pd.io.sql.DatabaseError as e:
        logger.error(f"Error loading data from database: {e}")
        raise
    finally:
        conn.close()
    
    return movies, ratings, tags

def initialize_database():
    logger.info("Initializing database...")
    import_csv_to_sqlite()
    logger.info("Database initialization complete.")

    # Verify that tables exist and have data
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        for table in ['movies', 'ratings', 'tags']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"Table '{table}' has {count} rows")
    except sqlite3.Error as e:
        logger.error(f"Error verifying tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
