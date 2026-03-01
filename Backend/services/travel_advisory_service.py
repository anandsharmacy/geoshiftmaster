from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class TravelAdvisoryService:
    def __init__(self):
        self.base_url = "https://www.smartraveller.gov.au/destinations-export"

    async def get_travel_advisory(self, country_code_iso2: str) -> Dict[str, Any]:
        country_code_iso2 = country_code_iso2.upper()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout to 30 seconds
                url = self.base_url
                logger.debug(f"Smartraveller API: Requesting URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Smartraveller API: Raw response for all destinations: {data}")

                advisory_data = None
                for country_advisory in data:
                    if country_advisory.get("iso_short_name") == country_code_iso2:
                        advisory_data = country_advisory
                        break

                if advisory_data:
                    # Assuming 'advice_level' maps to a score (e.g., 1-4 or 1-5)
                    # And 'advice_text' is the message
                    score_map = {
                        "Exercise normal safety precautions": 1.0,
                        "Exercise a high degree of caution": 2.0,
                        "Reconsider your need to travel": 3.0,
                        "Do not travel": 4.0
                    }
                    advice_level = advisory_data.get("advice_level")
                    score = score_map.get(advice_level, None)
                    message = advisory_data.get("advice_text")

                    if score is None:
                        logger.warning(f"Smartraveller API: Unknown advice_level '{advice_level}' for {country_code_iso2}. Defaulting score to None.")

                    return {
                        "score": score,
                        "message": message
                    }
                logger.warning(f"Smartraveller API: No data found for {country_code_iso2}")
                return {"score": None, "message": "No travel advisory data available"}
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartraveller API: HTTP error for {country_code_iso2}: {e}. Response: {e.response.text}")
            return {"score": None, "message": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"Smartraveller API: Request error for {country_code_iso2}: {e}")
            return {"score": None, "message": f"Request error: {e}"}
        except Exception as e:
            logger.error(f"Smartraveller API: An unexpected error occurred for {country_code_iso2}: {e}")
            return {"score": None, "message": f"Unexpected error: {e}"}