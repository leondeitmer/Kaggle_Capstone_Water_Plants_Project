import os
import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

def load_plant_database():
    """Loads the plant database JSON containing categories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "resources", "plant_database.json")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load plant database: {str(e)}")
        return {"categories": []}

def get_category_data(species_name, db):
    """Finds the matching category in the plant database."""
    categories = db.get("categories", [])
    
    # Map English UI species names to English database IDs
    mapping = {
        "water-loving herbs": "herbs_water_loving",
        "mediterranean herbs": "herbs_mediterranean",
        "succulents & cacti": "succulents_cacti",
        "thirsty flowers": "flowering_plants_thirsty",
        "normal flowers": "flowering_plants_normal",
        "thirsty vegetables": "vegetables_thirsty",
        "normal vegetables": "vegetables_normal",
        "fruits & berries": "fruits_berries",
        "mediterranean container plants": "container_plants_mediterranean",
        "climbing plants & ivy": "climbing_plants_ivy",
        "shade plants": "foliage_plants_shade_loving"
    }
    
    mapped_id = mapping.get(species_name.lower())
    if mapped_id:
        for cat in categories:
            if cat["id"] == mapped_id:
                return cat

    # Find exact match
    for cat in categories:
        if cat["name"].lower() == species_name.lower():
            return cat
            
    # Fallback to general categories if no direct match
    for cat in categories:
        if cat["id"] in species_name.lower() or species_name.lower() in cat["name"].lower():
            return cat
            
    # Default fallback category if nothing matches
    return {
        "name": "Generisch (Mittel)",
        "base_depletion_pct": 10,
        "optimal_sun_hours": 5
    }

def calculate_plant_moisture(plant: dict, balcony_config: dict, weather_data: dict) -> dict:
    """
    Executes the daily moisture depletion simulation for a single plant.
    Factors in baseline depletion, temperature, humidity, sun exposure, and rain.
    """
    db = load_plant_database()
    cat_data = get_category_data(plant.get("species", ""), db)
    
    base_depletion = cat_data.get("base_depletion_pct", 10)
    optimal_sun = cat_data.get("optimal_sun_hours", 5)
    
    last_watered_str = plant.get("lastWatered")
    plant_sun = plant.get("sunHours", balcony_config.get("defaultSunHours", 5))
    is_covered = balcony_config.get("isCovered", False)
    
    now = datetime.now(timezone.utc)
    
    # Parse last watered date
    try:
        last_watered = datetime.fromisoformat(last_watered_str.replace("Z", "+00:00"))
    except Exception as e:
        logger.error(f"Invalid lastWatered date format: {last_watered_str}. Error: {str(e)}")
        last_watered = now - timedelta(days=2)
        
    days_since = (now - last_watered).days
    
    # Run simulation day-by-day
    current_moisture = 100.0
    
    # Extract weather arrays from Open-Meteo response
    weather_times = weather_data.get("time", [])
    temps = weather_data.get("temperature_mean_c", [])
    humidities = weather_data.get("humidity_mean_percent", [])
    rains = weather_data.get("precipitation_sum_mm", [])
    
    # We simulate starting from the day after the last watering up to today
    for day_offset in range(1, days_since + 1):
        sim_date = (last_watered + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        # Default daily parameters if weather data is missing for this date
        t_mean = 20.0
        h_mean = 60.0
        rain_mm = 0.0
        
        # Match weather data for the simulated date
        if sim_date in weather_times:
            idx = weather_times.index(sim_date)
            t_mean = temps[idx] if temps[idx] is not None else 20.0
            h_mean = humidities[idx] if idx < len(humidities) and humidities[idx] is not None else 60.0
            rain_mm = rains[idx] if idx < len(rains) and rains[idx] is not None else 0.0
            
        # 1. Temperature Factor (F_temp = (Temp / 20.0) ** 3.5, minimum 0.2)
        f_temp = max(0.2, (t_mean / 20.0) ** 3.5)
        
        # 2. Sun Exposure Factor (F_sun = 1.0 + 0.15 * (S_plant - S_optimal), minimum 0.2)
        f_sun = max(0.2, 1.0 + 0.15 * (plant_sun - optimal_sun))
        
        # 3. Humidity Factor (F_humidity = 1.5 - Humidity / 100.0)
        f_humidity = 1.5 - (h_mean / 100.0)
        
        # 4. Rain Bonus (adds moisture if balcony is open)
        rain_bonus = 0.0
        if not is_covered and rain_mm > 0:
            rain_bonus = rain_mm * 15.0  # 1mm rain = +15% moisture
            
        # Calculate daily depletion
        daily_depletion = (base_depletion * f_temp * f_sun * f_humidity) - rain_bonus
        
        # Apply depletion and clamp moisture between 0% and 100%
        current_moisture = max(0.0, min(100.0, current_moisture - daily_depletion))

    # Categorize watering status
    moisture_val = int(round(current_moisture))
    if moisture_val < 35:
        status = "Water Now"
        next_water_date = now.strftime("%Y-%m-%d")
    elif moisture_val < 60:
        status = "Water Soon"
        next_water_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        status = "Healthy"
        
        # Estimate next watering date by projecting forward using average depletion
        # Use average daily depletion simulated or default base depletion adjusted
        avg_depletion = max(1.0, (100.0 - current_moisture) / days_since) if days_since > 0 else (base_depletion * 1.0)
        days_remaining = max(1, int(round((current_moisture - 55.0) / avg_depletion)))
        next_water_date = (now + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
        
    return {
        "plant_id": plant.get("id"),
        "moisture_level": moisture_val,
        "status": status,
        "next_watering_date": next_water_date
    }

def calculate_plants_moisture(balcony_config: dict, plants: list, weather_data: dict) -> list:
    """Calculates soil moisture levels for a batch of plants."""
    results = []
    for plant in plants:
        results.append(calculate_plant_moisture(plant, balcony_config, weather_data))
    return results
