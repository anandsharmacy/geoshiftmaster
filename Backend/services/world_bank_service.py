from typing import Dict, Any, Optional
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

class WorldBankService:
    def __init__(self):
        self.base_url = "https://api.worldbank.org/v2/country"
        self.indicators = {
            "life_expectancy": "SP.DYN.LE00.IN",
            "gdp_per_capita": "NY.GDP.PCAP.CD",
            "population": "SP.POP.TOTL",
        }

    async def _fetch_indicator(self, country_code: str, indicator_code: str) -> Any:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/{country_code}/indicator/{indicator_code}?format=json"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 1 and data[1]:
                    for entry in data[1]:
                        if entry.get("value") is not None:
                            return entry["value"]
                logger.warning(f"World Bank API: No data found for {indicator_code} for {country_code}")
                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"World Bank API: HTTP error for {indicator_code} for {country_code}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"World Bank API: Request error for {indicator_code} for {country_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"World Bank API: An unexpected error occurred for {indicator_code} for {country_code}: {e}")
            return None

    async def get_country_metrics(self, country_code: str) -> Dict[str, Optional[float]]:
        tasks = [
            self._fetch_indicator(country_code, self.indicators["life_expectancy"]),
            self._fetch_indicator(country_code, self.indicators["gdp_per_capita"]),
            self._fetch_indicator(country_code, self.indicators["population"]),
        ]

        life_expectancy, gdp_per_capita, population = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        return {
            "life_expectancy": life_expectancy if not isinstance(life_expectancy, Exception) else None,
            "gdp_per_capita": gdp_per_capita if not isinstance(gdp_per_capita, Exception) else None,
            "population": population if not isinstance(population, Exception) else None,
        }