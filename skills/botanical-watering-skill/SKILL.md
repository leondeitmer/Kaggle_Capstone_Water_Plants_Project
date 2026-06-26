---
name: botanical-watering-skill
description: Botanical reasoning guidelines and mathematical criteria for AI agents to evaluate plant water levels based on local weather parameters, sun exposure, and the reference database resources/plant_database.json.
---

# Botanical Watering Skill

This skill defines the botanical reasoning framework and calculations used by the AI agent to estimate plant soil moisture and suggest optimal watering schedules.

---

## 1. Reference Plant Database

The agent utilizes the plant lookup database located in the skill resources folder at `resources/plant_database.json`. This database defines the standard baseline metrics for the 50 most common balcony plants:
- `base_depletion_pct`: The average percentage of soil moisture lost daily under baseline conditions (20°C, average humidity, and optimal sun exposure).
- `optimal_sun_hours`: The standard daily sun exposure expected for this species.

---

## 2. Soil Moisture Depletion Model

To estimate a plant's current soil moisture level ($M_{\text{current}}$), the agent performs a daily simulation starting from the day after the last watering ($M = 100\%$) up to the current day. 

For each day $d$ in the weather history:

$$M_{d} = M_{d-1} - \text{DailyDepletion}_{d}$$

Where the daily moisture depletion rate ($\text{DailyDepletion}_{d}$) is calculated as:

$$\text{DailyDepletion}_{d} = B \times F_{\text{temp}} \times F_{\text{sun}} \times F_{\text{humidity}} - \text{RainBonus}_{d}$$

### Parameters & Factors:
1.  **Base Depletion ($B$):** Loaded from `resources/plant_database.json` matching the plant species.
    *   *If the plant species is not in the database:* Match it to the closest family or category (e.g., Herb, Succulent, Vegetable, Flower) and estimate a comparable $B$ (Low = 5%, Medium = 10%, High = 16%, Very High = 22%).
2.  **Temperature Factor ($F_{\text{temp}}$):** Calculated from the day's mean temperature ($T_{\text{mean}}$):
    *   $F_{\text{temp}} = T_{\text{mean}} / 20.0$ (restricted to a minimum of 0.2 in freezing weather).
3.  **Sun Exposure Factor ($F_{\text{sun}}$):** Combines the plant's configured sun hours ($S_{\text{plant}}$) and the species optimal sun hours ($S_{\text{optimal}}$):
    *   $F_{\text{sun}} = 1.0 + 0.1 \times (S_{\text{plant}} - S_{\text{optimal}})$
4.  **Humidity Factor ($F_{\text{humidity}}$):** Calculated from the day's mean relative humidity ($H_{\text{mean}}$):
    *   $F_{\text{humidity}} = 1.5 - (H_{\text{mean}} / 100.0)$
5.  **Rain Bonus ($\text{RainBonus}_{d}$):**
    *   *If the balcony is covered:* $\text{RainBonus}_{d} = 0\%$
    *   *If the balcony is open:* $\text{RainBonus}_{d} = \text{Precipitation (mm)} \times 15\%$ (e.g., 2mm of rain adds $30\%$ moisture).

*Note: Soil moisture is clamped between $0\%$ and $100\%$ at the end of each simulated day.*

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
- Mention if the plant's sun exposure settings or balcony coverage impacted the outcome.
