from typing import Dict, Any, Optional, Tuple
import asyncio
import logging
from .external_clients import ExternalClients
from .cache_manager import (
    get_cached,
    set_cache,
    is_in_flight,
    get_in_flight,
    set_in_flight,
    remove_in_flight,
)

from Backend.scoring.weighting_engine import get_weights
from Backend.scoring.scoring_engine import score_country

logger = logging.getLogger(__name__)

async def _fetch_and_build(
    country_code: str, risk_tolerance: str, duration: str, debug_mode: bool = False
) -> Tuple[Dict[str, Any], bool, list]: # Returns (result, is_cache_hit, missing_metrics)

    async with ExternalClients() as external_clients:
        missing_metrics = []

        # 1. Fetch country profile to get basic data and lat/lon
        country_profile_data = await external_clients.fetch_country_profile(country_code)
        if not country_profile_data:
            logger.error(f"Failed to fetch country profile for {country_code}. Cannot proceed with analysis.")
            return {}, False, ["country_profile"]

        iso2_code = country_profile_data.get("iso2")
        lat = country_profile_data.get("lat")
        lon = country_profile_data.get("lon")
        population = country_profile_data.get("population")

        if not iso2_code:
            logger.error(f"Country profile for {country_code} is missing ISO2 code. Cannot proceed.")
            return {}, False, ["iso2_code"]

        # Run external API calls concurrently
        results = await asyncio.gather(
            external_clients.fetch_worldbank_health(country_code),
            external_clients.fetch_travel_advisory(country_profile_data.get("country_name")),
            external_clients.fetch_weather(lat, lon),
            external_clients.fetch_aqi(lat, lon),
            return_exceptions=True,
        )

        world_bank_metrics_data = results[0] if not isinstance(results[0], Exception) else {}
        travel_advisory_data = results[1] if not isinstance(results[1], Exception) else {}
        weather_data = results[2] if not isinstance(results[2], Exception) else {}
        aqi_data = results[3] if not isinstance(results[3], Exception) else {}

        # Log exceptions if any occurred
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                service_name = ["World Bank", "Travel Advisory", "Weather", "AQI"][i]
                logger.error(f"Error fetching data from {service_name} for {country_code}: {res}")

        # Raw metrics used internally for scoring
        raw_metrics = {
            "life_expectancy": world_bank_metrics_data.get("life_expectancy"),
            "gdp_per_capita": world_bank_metrics_data.get("gdp_per_capita"),
            "population": population,
            "pm25": aqi_data.get("aqi"), # Open-Meteo AQI only provides US AQI, not separate PM2.5/PM10
            "pm10": aqi_data.get("aqi"), # Using AQI as PM10 for now, as Open-Meteo only provides US AQI
            "travel_advisory_score": travel_advisory_data.get("advisory_score"),
            "temperature": weather_data.get("temperature"),
            "humidity": None, # Open-Meteo Weather does not provide humidity
        }

        # Track missing raw metrics
        for metric_name, value in raw_metrics.items():
            if value is None:
                missing_metrics.append(metric_name)

        # Normalize to 0–100, handling None values
        normalized_scores = _normalize_metrics(raw_metrics)

        # Calculate sub_scores (0-100 scale)
        # travel_risk_sub_score: higher is riskier (0-100)
        travel_risk_sub_score = (1 - normalized_scores.get("travel_advisory_score", 0.5)) * 100
        # health_infra_score: higher is better (0-100)
        health_infra_score = (normalized_scores.get("life_expectancy", 0.5) + normalized_scores.get("gdp_per_capita", 0.5)) / 2 * 100
        # env_stability_score: higher is better (0-100)
        env_stability_score = (normalized_scores.get("pm25", 0.5) + normalized_scores.get("pm10", 0.5) + normalized_scores.get("temperature", 0.5)) / 3 * 100

        # Round final score to 1 decimal place
        # overall_score = round(overall_score, 1) # This line was removed, will be re-added after dynamic scoring

        # Use dynamic weighting and scoring engines
        weights = get_weights(risk_tolerance, duration)

        metrics_for_scoring = {
            "life_expectancy": normalized_scores.get("life_expectancy"),
            "gdp_per_capita": normalized_scores.get("gdp_per_capita"),
            "population": normalized_scores.get("population"),
            "pm25": normalized_scores.get("pm25"),
            "pm10": normalized_scores.get("pm10"),
            "travel_advisory_score": normalized_scores.get("travel_advisory_score"),
            "temperature": normalized_scores.get("temperature"),
            "humidity": normalized_scores.get("humidity"),
        }

        overall_score = score_country(metrics_for_scoring, weights)
        overall_score = round(overall_score, 1)

        explanation = f"Overall score of {overall_score:.1f} based on risk tolerance '{risk_tolerance}' and duration '{duration}'. " \
                      f"Travel risk: {round(travel_risk_sub_score, 0):.0f}, Health infrastructure: {round(health_infra_score, 0):.0f}, Environmental stability: {round(env_stability_score, 0):.0f}."

        result = {
            "country_code": country_code,
            "country_name": country_profile_data.get("country_name"),
            "overall_score": overall_score,
            "sub_scores": {
                "travel_risk": round(travel_risk_sub_score, 0),
                "health_infra": round(health_infra_score, 0),
                "env_stability": round(env_stability_score, 0),
            },
            "explanation": explanation,
        }

        # Add debug information if debug_mode is enabled
        if debug_mode:
            result["debug_analysis"] = {
                "weights_used": weights,
                "raw_metrics": raw_metrics,
                "normalized_metrics": normalized_scores,
            }
            logger.debug(f"[{country_code}] Debug Analysis: {result['debug_analysis']}")
            logger.debug(f"[{country_code}] Raw Metrics: {raw_metrics}")
            logger.debug(f"[{country_code}] Normalized Scores: {normalized_scores}")
            logger.debug(f"[{country_code}] Final Overall Score: {overall_score}")

        return result, False, missing_metrics


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

def _normalize_pm10(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    return 1.0 - min(value / 100, 1.0) # Assuming similar normalization for PM10

def _normalize_travel_advisory_score(value: Optional[float]) -> float:
    if value is None:
        return 0.2 # Conservative default: lower safety score if data is missing
    return 1.0 - (value / 100.0) # Score is now 0-100

def _normalize_temperature(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    if 15 <= value <= 28:
        return 1.0
    elif value < 15:
        return max(0.0, 1.0 - (15 - value) / 15)
    else: # value > 28
        return max(0.0, 1.0 - (value - 28) / 12)

def _normalize_humidity(value: Optional[float]) -> float:
    if value is None:
        return 0.5
    # Open-Meteo Weather does not provide humidity, so this will always be 0.5
    return 0.5

def _normalize_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
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


def _get_weights(risk_tolerance: str, duration: str) -> Dict[str, float]:
    # Base weights for moderate risk tolerance
    weights = {
        "life_expectancy": 0.20,
        "gdp_per_capita": 0.20,
        "population": 0.10,
        "pm25": 0.15,
        "travel_advisory_score": 0.15,
        "temperature": 0.10,
        "humidity": 0.10,
    }

    # Adjust weights based on risk tolerance
    if risk_tolerance == "low":
        weights["life_expectancy"] = 0.20
        weights["gdp_per_capita"] = 0.15
        weights["population"] = 0.05
        weights["pm25"] = 0.20
        weights["travel_advisory_score"] = 0.25
        weights["temperature"] = 0.15
        weights["humidity"] = 0.00
    elif risk_tolerance == "high":
        weights["life_expectancy"] = 0.20
        weights["gdp_per_capita"] = 0.30
        weights["population"] = 0.15
        weights["pm25"] = 0.10
        weights["travel_advisory_score"] = 0.10
        weights["temperature"] = 0.15
        weights["humidity"] = 0.00

    # Apply duration adjustments as multipliers
    if duration == "short-term":
        weights["temperature"] *= 1.2
        weights["humidity"] *= 1.1
        weights["pm25"] *= 1.2
        weights["travel_advisory_score"] *= 1.2
        weights["life_expectancy"] *= 0.8
        weights["population"] *= 0.8
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


def _score_country(metrics: Dict[str, float], weights: Dict[str, float]) -> float:
    score = 0.0

    for metric_name, metric_value in metrics.items():
        weight = weights.get(metric_name, 0.0)
        score += metric_value * weight

    return round(score * 100, 2)


async def analyze_country(
    country_code: str, risk_tolerance: str, duration: str, debug_mode: bool = False
) -> Tuple[Dict[str, Any], bool, list]:
    cache_key = f"{country_code}_{risk_tolerance}_{duration}"

    # 1️⃣ Check cache
    cached_result = get_cached(cache_key)
    if cached_result is not None:
        return cached_result, True, [] # Return cached result, True for cache hit, empty missing_metrics

    # 2️⃣ If already being fetched, wait for it
    if is_in_flight(cache_key):
        return await get_in_flight(cache_key), False, [] # Return in-flight result, False for cache miss, empty missing_metrics

    # 3️⃣ Otherwise create task
    task = asyncio.create_task(
        _fetch_and_build(country_code, risk_tolerance, duration, debug_mode)
    )
    set_in_flight(cache_key, task)

    try:
        result, is_cache_hit, missing_metrics = await task
        set_cache(cache_key, result)
        return result, is_cache_hit, missing_metrics
    finally:
        remove_in_flight(cache_key)