from typing import Dict

def get_weights(risk_tolerance: str, duration: str) -> Dict[str, float]:
    # Base weights for moderate risk tolerance
    weights = {
        "life_expectancy": 0.20,
        "gdp_per_capita": 0.20,
        "population": 0.10,
        "pm25": 0.15,
        "travel_advisory_score": 0.25,
        "temperature": 0.10,
        "humidity": 0.10,
    }

    # Adjust weights based on risk tolerance
    if risk_tolerance == "low":
        weights["life_expectancy"] = 0.20
        weights["gdp_per_capita"] = 0.15
        weights["population"] = 0.05
        weights["pm25"] = 0.20
        weights["travel_advisory_score"] = 0.35
        weights["temperature"] = 0.15
        weights["humidity"] = 0.00 # Not explicitly mentioned, so setting to 0
    elif risk_tolerance == "high":
        weights["life_expectancy"] = 0.20
        weights["gdp_per_capita"] = 0.30
        weights["population"] = 0.15
        weights["pm25"] = 0.10
        weights["travel_advisory_score"] = 0.10
        weights["temperature"] = 0.15
        weights["humidity"] = 0.00 # Not explicitly mentioned, so setting to 0

    # Apply duration adjustments as multipliers
    if duration == "short-term":
        weights["temperature"] *= 1.2
        weights["humidity"] *= 1.1
        weights["pm25"] *= 1.2
        weights["travel_advisory_score"] *= 1.2
        weights["life_expectancy"] *= 0.8
        weights["population"] *= 0.8
        # gdp_per_capita remains unchanged
    elif duration == "long-term":
        weights["life_expectancy"] *= 1.2
        weights["gdp_per_capita"] *= 1.2
        weights["population"] *= 1.2
        weights["temperature"] *= 0.8
        weights["humidity"] *= 0.9
        weights["pm25"] *= 0.9
        weights["travel_advisory_score"] *= 0.9

    # Re-normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    if total_weight > 0:
        for key in weights:
            weights[key] /= total_weight

    return weights