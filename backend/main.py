import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

from backend.agents import analyze_plants_watering

app = FastAPI(title="FloraCast API", version="1.0.0")

# Setup CORS to allow Vite development server to query the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request schemas
class BalconyConfig(BaseModel):
    city: str
    zipCode: str
    defaultSunHours: float
    isCovered: bool

class PlantItem(BaseModel):
    id: str
    name: str
    species: str
    lastWatered: str
    sunHours: float
    imageUrl: str = ""
    description: str = ""
    rainExposure: bool = False

class AnalyzeRequest(BaseModel):
    balconyConfig: BalconyConfig
    plants: List[PlantItem]

@app.post("/api/analyze")
async def analyze_plants(request: AnalyzeRequest):
    # Ensure GEMINI_API_KEY is available
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY is not set on the server. Please configure it in environment variables."
        )
        
    try:
        # Convert Pydantic models to dictionaries
        balcony_dict = request.balconyConfig.model_dump()
        plants_list = [plant.model_dump() for plant in request.plants]
        
        # Run agent analysis
        results = await analyze_plants_watering(balcony_dict, plants_list)
        return {"success": True, "analyses": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Mount static files for unified production build if static directory exists
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    # Quick health check for development
    @app.get("/")
    def read_root():
        return {"message": "FloraCast API is running. Vite static files directory not found (expected in backend/static)."}
