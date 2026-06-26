---
name: botanical-watering-skill
description: Botanical reasoning guidelines and mathematical criteria for AI agents to evaluate plant water levels based on local weather parameters, sun exposure, and the reference database resources/plant_database.json.
---

# Botanical Watering Skill

This skill defines the botanical reasoning framework and calculations used by the AI agent to estimate plant soil moisture and suggest optimal watering schedules.

---

## 1. Reference Plant Database

The agent utilizes the plant category database located in the skill resources folder at `resources/plant_database.json`. This database defines the standard baseline metrics for the primary plant categories:
- `base_depletion_pct`: The average percentage of soil moisture lost daily under baseline conditions (20°C, average humidity, and optimal sun exposure).
- `optimal_sun_hours`: The standard daily sun exposure expected for this category.

---

## 2. Soil Moisture Depletion Model (Conceptual)

The soil moisture level is calculated deterministically in Python (by simulating daily water loss starting from 100% after watering down to the current day). 

To write accurate German explanations, you should understand the conceptual relationships behind the calculations:
1.  **Baseline Consumption:** Each plant category has a baseline daily water depletion rate (e.g., water-loving herbs dry out quickly, while succulents lose very little moisture).
2.  **Temperature Impact:** Higher temperatures accelerate drying (proportional to deviation from 20°C), while cooler weather slows it down.
3.  **Sun Exposure Impact:** For every hour that the plant's configured sun exposure exceeds the category's optimal sun hours, evaporation increases by 15%. Conversely, shade decreases water needs by 15% per hour of deficit.
4.  **Humidity Impact:** Dry air (lower relative humidity) increases evaporation, while moist air slows it down.
5.  **Precipitation (Rain):** If the balcony is open (not covered), rain adds moisture to the soil (1mm of rain adds roughly 15% moisture). If the balcony is covered, rain is ignored.

---

## 3. Status Categorization & Predictions

- **Healthy:** Moisture level $\ge 50\%$. Next watering is calculated as the projected day when moisture drops below $30\%$.
- **Water Soon:** Moisture level between $25\%$ and $49\%$. Next watering date is set to tomorrow.
- **Water Now:** Moisture level $< 25\%$ or watering is severely overdue. Next watering date is set to today.

---

## 4. Explanation Writing Style (German)

The agent must output a concise 1-2 sentence German explanation summarizing the reasoning:
- Cite the estimated moisture level.
- Mention recent weather parameters (e.g., high temperatures, low humidity, or rain).
- **Sun Exposure Impact:** Explicitly mention if the plant's actual sun hours deviate from the optimal sun hours for its category (e.g., "Da die Pflanze mit 8 Std. Sonne mehr Licht bekommt als die optimalen 5 Std., verdunstet sie Wasser schneller." or "Der halbschattige Standort (2 Std. statt 5 Std. Sonne) reduziert den Wasserbedarf.").
- Mention if the balcony coverage (covered vs. open) and recent rain impacted the soil moisture.

---

## 5. Implementation Script Reference

- The mathematical model described above is implemented in the executable script located at [moisture_calculator.py](scripts/moisture_calculator.py) in the `scripts/` directory. The main backend dynamically loads and executes this script to calculate soil moisture values before requesting explanations.
