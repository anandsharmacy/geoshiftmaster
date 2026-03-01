from typing import Dict, Any
import httpx
import os
import asyncio

class OpenWeatherService:
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "OPENWEATHER_API_KEY") # Placeholder for now

    async def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            weather_url = f"{self.base_url}/weather?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
            air_pollution_url = f"{self.base_url}/air_pollution?lat={lat}&lon={lon}&appid={self.api_key}"

            weather_response, air_pollution_response = await asyncio.gather(
                client.get(weather_url),
                client.get(air_pollution_url),
                return_exceptions=True
            )

            weather_data = weather_response.json() if not isinstance(weather_response, Exception) else {}
            air_pollution_data = air_pollution_response.json() if not isinstance(air_pollution_response, Exception) else {}

            return {
                "temperature": weather_data.get("main", {}).get("temp"),
                "humidity": weather_data.get("main", {}).get("humidity"),
                "aqi": air_pollution_data.get("list", [{}])[0].get("main", {}).get("aqi")
            }