import os
import sqlite3
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load local .env file from project root if it exists
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

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

# Initialize SQLite audit DB
def init_audit_db():
    try:
        conn = sqlite3.connect("audit_logs.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                plant_name TEXT,
                species TEXT,
                status TEXT,
                moisture_level INTEGER,
                watered_by_rain BOOLEAN
            )
        """)
        conn.commit()
        conn.close()
        logger.info("SQLite audit DB initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize SQLite audit DB: {e}")

init_audit_db()

def log_analysis(plant_name: str, species: str, status: str, moisture_level: int, watered_by_rain: bool):
    try:
        conn = sqlite3.connect("audit_logs.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (plant_name, species, status, moisture_level, watered_by_rain)
            VALUES (?, ?, ?, ?, ?)
        """, (plant_name, species, status, moisture_level, watered_by_rain))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log analysis to audit DB: {e}")

# Optional API Key Authentication
API_KEY = os.getenv("FLORAWAVE_API_KEY")

def verify_api_key(request: Request):
    if API_KEY:
        header_key = request.headers.get("X-API-Key")
        if header_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid or missing X-API-Key header.")

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )

@app.post("/api/analyze")
async def analyze_plants(request: Request, analyze_request: AnalyzeRequest):
    # Verify API key if configured
    verify_api_key(request)

    # Ensure GEMINI_API_KEY is available
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500, 
            detail="GEMINI_API_KEY is not set on the server. Please configure it in environment variables."
        )
        
    # Convert Pydantic models to dictionaries
    balcony_dict = analyze_request.balconyConfig.model_dump()
    plants_list = [plant.model_dump() for plant in analyze_request.plants]
    
    # Run agent analysis
    results = await analyze_plants_watering(balcony_dict, plants_list)
    
    # Log to audit DB
    for res in results:
        plant_item = next((p for p in analyze_request.plants if p.id == res.get("plant_id")), None)
        log_analysis(
            plant_name=plant_item.name if plant_item else "Unknown",
            species=plant_item.species if plant_item else "Unknown",
            status=res.get("status", "Unknown"),
            moisture_level=res.get("moisture_level", 0),
            watered_by_rain=res.get("watered_by_rain", False)
        )
        
    return {"success": True, "analyses": results}

# Mount static files for unified production build if static directory exists
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    # Quick health check for development
    @app.get("/")
    def read_root():
        return {"message": "FloraCast API is running. Vite static files directory not found (expected in backend/static)."}
