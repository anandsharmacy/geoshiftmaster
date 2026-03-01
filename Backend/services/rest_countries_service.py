from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class RestCountriesService:
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1/alpha"

    async def get_country_profile(self, country_code: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/{country_code}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data and isinstance(data, list) and len(data) > 0:
                    country_data = data[0]
                    return {
                        "name": country_data.get("name", {}).get("common"),
                        "region": country_data.get("region"),
                        "capital": country_data.get("capital", ["N/A"])[0] if country_data.get("capital") else None,
                        "currency": list(country_data.get("currencies", {}).keys())[0] if country_data.get("currencies") else None,
                        "flag": country_data.get("flags", {}).get("png"),
                        "latlng": country_data.get("latlng", [0, 0])
                    }
                logger.warning(f"REST Countries API: No data found for {country_code}")
                return {}
        except httpx.HTTPStatusError as e:
            logger.error(f"REST Countries API: HTTP error for {country_code}: {e}")
            return {}
        except httpx.RequestError as e:
            logger.error(f"REST Countries API: Request error for {country_code}: {e}")
            return {}
        except Exception as e:
            logger.error(f"REST Countries API: An unexpected error occurred for {country_code}: {e}")
            return {}