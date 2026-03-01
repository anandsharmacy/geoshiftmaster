from typing import Dict, Any
import httpx
import os
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY environment variable not set. Weather data may be unavailable.")

    async def get_weather_data(self, city_name: str) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning(f"OpenWeather API: Skipping API call for {city_name} due to missing API key.")
            return {"temperature": None, "humidity": None, "description": "API key missing"}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}?q={city_name}&units=metric&appid={self.api_key}"
                logger.debug(f"OpenWeather API: Requesting URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"OpenWeather API: Raw response for {city_name}: {data}")

                return {
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "description": data.get("weather", [{}])[0].get("description")
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenWeather API: HTTP error for city={city_name}: {e}. Response: {e.response.text}")
            return {"temperature": None, "humidity": None, "description": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"OpenWeather API: Request error for city={city_name}: {e}")
            return {"temperature": None, "humidity": None, "description": f"Request error: {e}"}
        except Exception as e:
            logger.error(f"OpenWeather API: An unexpected error occurred for city={city_name}: {e}. Raw response: {data if 'data' in locals() else 'N/A'}")
            return {"temperature": None, "humidity": None, "description": f"Unexpected error: {e}"}