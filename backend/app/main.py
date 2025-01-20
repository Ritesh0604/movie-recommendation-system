from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.recommendation import get_movie_recommendations
from app.database import initialize_database
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the database
logger.info("Initializing database...")
initialize_database()
logger.info("Database initialization complete.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MovieRequest(BaseModel):
    movies: list[str]

@app.post("/recommendations")
async def get_recommendations(request: MovieRequest):
    logger.info(f"Received request with movies: {request.movies}")
    
    if not request.movies:
        raise HTTPException(status_code=400, detail="No movies provided")
    
    recommendations = get_movie_recommendations(request.movies)
    
    if not recommendations:
        logger.warning("No recommendations found")
        return {"recommendations": [], "message": "No recommendations found. Try different movie titles."}
    
    logger.info(f"Returning recommendations: {recommendations}")
    return {"recommendations": recommendations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
