from typing import Dict, Any, Optional

def _normalize_life_expectancy(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return max(0.0, min(1.0, (value - 50) / 35))

def _normalize_gdp_per_capita(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return min(value / 80000, 1.0)

def _normalize_population(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return 1.0 - min(value / 1_500_000_000, 1.0)

def _normalize_pm25(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return 1.0 - min(value / 100, 1.0)

def _normalize_travel_advisory_score(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return 1.0 - (value / 5.0)

def _normalize_temperature(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    if 15 <= value <= 28:
        return 1.0
    elif value < 15:
        return max(0.0, 1.0 - (15 - value) / 15) # Scales from 0 at 0C to 1 at 15C
    else: # value > 28
        return max(0.0, 1.0 - (value - 28) / 12) # Scales from 0 at 40C to 1 at 28C

def _normalize_humidity(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    if 30 <= value <= 70:
        return 1.0
    elif value < 30:
        return max(0.0, value / 30) # Scales from 0 at 0% to 1 at 30%
    else: # value > 70
        return max(0.0, 1.0 - (value - 70) / 30) # Scales from 0 at 100% to 1 at 70%

def normalize_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}

    normalized["life_expectancy"] = _normalize_life_expectancy(metrics.get("life_expectancy"))
    normalized["gdp_per_capita"] = _normalize_gdp_per_capita(metrics.get("gdp_per_capita"))
    normalized["population"] = _normalize_population(metrics.get("population"))
    normalized["pm25"] = _normalize_pm25(metrics.get("pm25"))
    normalized["pm10"] = _normalize_pm10(metrics.get("pm10"))
    normalized["travel_advisory_score"] = _normalize_travel_advisory_score(metrics.get("travel_advisory_score"))
    normalized["temperature"] = _normalize_temperature(metrics.get("temperature"))
    normalized["humidity"] = _normalize_humidity(metrics.get("humidity"))

    return normalized
