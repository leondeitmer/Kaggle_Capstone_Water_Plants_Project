import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("FloraCast Weather Service")

GEO_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

@mcp.tool()
async def geocode_location(city: str, zip_code: str = "") -> dict:
    """
    Resolve a city and optional zip code (PLZ) to latitude and longitude coordinates.
    
    Args:
        city: Name of the city (e.g. "Berlin")
        zip_code: Optional zip code / postal code (e.g. "10117")
        
    Returns:
        A dict containing 'latitude', 'longitude', and 'display_name', or an error message.
    """
    query = f"{zip_code} {city}".strip()
    params = {
        "name": query,
        "count": 1,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(GEO_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if "results" not in data or not data["results"]:
                return {"error": f"Location '{query}' could not be resolved."}
            
            result = data["results"][0]
            display_name = f"{result['name']}, {result.get('country', '')}"
            return {
                "latitude": float(result["latitude"]),
                "longitude": float(result["longitude"]),
                "display_name": display_name
            }
    except Exception as e:
        return {"error": f"Geocoding failed: {str(e)}"}

@mcp.tool()
async def get_weather_history_and_forecast(latitude: float, longitude: float, past_days: int = 14) -> dict:
    """
    Fetch historical daily weather data (temperature, humidity, precipitation) for the past days.
    
    Args:
        latitude: The latitude coordinate
        longitude: The longitude coordinate
        past_days: Number of past days to retrieve (default: 14)
        
    Returns:
        A dict containing daily weather metrics (time, temperature, humidity, precipitation).
    """
    # Restrict past_days between 1 and 90 to match Open-Meteo's limitations
    past_days = max(1, min(past_days, 90))
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": past_days,
        "forecast_days": 1,
        "daily": "temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum",
        "timezone": "auto"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if "daily" not in data:
                return {"error": "Weather data structure is invalid."}
            
            daily_data = data["daily"]
            return {
                "time": daily_data["time"],
                "temperature_mean_c": daily_data["temperature_2m_mean"],
                "humidity_mean_percent": daily_data["relative_humidity_2m_mean"],
                "precipitation_sum_mm": daily_data["precipitation_sum"]
            }
    except Exception as e:
        return {"error": f"Weather API request failed: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
