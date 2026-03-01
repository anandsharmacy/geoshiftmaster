from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class AirQualityService:
    def __init__(self):
        self.base_url = "https://api.openaq.org/v3/locations"

    async def get_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                # Search for locations near the given coordinates
                url = f"{self.base_url}?coordinates={lat},{lon}&radius=10000&limit=10" # 10km radius, up to 10 locations
                logger.debug(f"OpenAQ API: Requesting URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"OpenAQ API: Raw response for lat={lat}, lon={lon}: {data}")

                pm25 = None
                pm10 = None

                if data and data.get("results"):
                    for location in data["results"]:
                        for sensor in location.get("sensors", []):
                            for measure in sensor.get("measurements", []):
                                if measure.get("parameter") == "pm25" and measure.get("value") is not None:
                                    pm25 = measure["value"]
                                if measure.get("parameter") == "pm10" and measure.get("value") is not None:
                                    pm10 = measure["value"]
                                if pm25 is not None and pm10 is not None:
                                    break # Found both, no need to continue
                            if pm25 is not None and pm10 is not None:
                                break
                        if pm25 is not None and pm10 is not None:
                            break

                if pm25 is None and pm10 is None:
                    logger.warning(f"OpenAQ API: No air quality data found for lat={lat}, lon={lon}")

                return {
                    "pm25": pm25,
                    "pm10": pm10
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAQ API: HTTP error for city={city_name}: {e}. Response: {e.response.text}")
            return {"pm25": None, "pm10": None}
        except httpx.RequestError as e:
            logger.error(f"OpenAQ API: Request error for city={city_name}: {e}")
            return {"pm25": None, "pm10": None}
        except Exception as e:
            logger.error(f"OpenAQ API: An unexpected error occurred for city={city_name}: {e}")
            return {"pm25": None, "pm10": None}