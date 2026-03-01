from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

class CountryNormalizerService:
    def __init__(self):
        self.base_url = "https://restcountries.com/v3.1/alpha"

    async def normalize_country(self, iso3_code: str) -> Optional[Dict[str, str]]:
        iso3_code = iso3_code.upper()
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/{iso3_code}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data and isinstance(data, list) and len(data) > 0:
                    country_data = data[0]
                    currencies = country_data.get("currencies")
                    currency_code = list(currencies.keys())[0] if currencies else None

                    return {
                        "iso2": country_data.get("cca2"),
                        "iso3": country_data.get("cca3"),
                        "name": country_data.get("name", {}).get("common"),
                        "capital": country_data.get("capital", ["N/A"])[0] if country_data.get("capital") else None,
                        "region": country_data.get("region"),
                        "currency": currency_code,
                        "flag": country_data.get("flags", {}).get("png"),
                        "latlng": country_data.get("latlng")
                    }
                logger.warning(f"Country Normalizer: No data found for {iso3_code} from REST Countries API.")
                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Country Normalizer: HTTP error for {iso3_code}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Country Normalizer: Request error for {iso3_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Country Normalizer: An unexpected error occurred for {iso3_code}: {e}")
            return None