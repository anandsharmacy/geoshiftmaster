from typing import Dict, Any, Optional
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)

class ExternalClients:
    def __init__(self):
        self.rest_countries_base_url = "https://restcountries.com/v3.1/alpha"
        self.worldbank_base_url = "https://api.worldbank.org/v2/country"
        self.open_meteo_weather_base_url = "https://api.open-meteo.com/v1/forecast"
        self.open_meteo_aqi_base_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.travel_advisory_base_url = "https://travel.state.gov/_res/rss/TAsTWs.xml"
        self.client = httpx.AsyncClient(timeout=10.0) # Shared client with a default timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def fetch_country_profile(self, country_code: str) -> Dict[str, Any]:
        try:
            url = f"{self.rest_countries_base_url}/{country_code}"
            logger.debug(f"REST Countries API: Requesting URL: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"REST Countries API: Raw response for {country_code}: {data}")

            if data and isinstance(data, list) and len(data) > 0:
                country_data = data[0]
                latlng = country_data.get("latlng", [0, 0])
                currencies = country_data.get("currencies")
                currency_code = list(currencies.keys())[0] if currencies else None

                return {
                    "country_name": country_data.get("name", {}).get("common", country_code),
                    "capital": country_data.get("capital", ["N/A"])[0] if country_data.get("capital") else None,
                    "lat": latlng[0] if len(latlng) > 0 else 0,
                    "lon": latlng[1] if len(latlng) > 1 else 0,
                    "iso2": country_data.get("cca2"),
                    "region": country_data.get("region"),
                    "currency": currency_code,
                    "flag": country_data.get("flags", {}).get("png"),
                    "population": country_data.get("population"),
                }
            logger.warning(f"REST Countries API: No data found for {country_code}.")
            return {
                "country_name": country_code,
                "capital": None,
                "lat": 0,
                "lon": 0,
                "iso2": None,
                "region": None,
                "currency": None,
                "flag": None,
                "population": None,
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"REST Countries API: HTTP error for {country_code}: {e}. Response: {e.response.text}")
            return {
                "country_name": country_code,
                "capital": None,
                "lat": 0,
                "lon": 0,
                "iso2": None,
                "region": None,
                "currency": None,
                "flag": None,
                "population": None,
            }
        except httpx.RequestError as e:
            logger.error(f"REST Countries API: Request error for {country_code}: {e}")
            return {
                "country_name": country_code,
                "capital": None,
                "lat": 0,
                "lon": 0,
                "iso2": None,
                "region": None,
                "currency": None,
                "flag": None,
                "population": None,
            }
        except Exception as e:
            logger.error(f"REST Countries API: An unexpected error occurred for {country_code}: {e}")
            return {
                "country_name": country_code,
                "capital": None,
                "lat": 0,
                "lon": 0,
                "iso2": None,
                "region": None,
                "currency": None,
                "flag": None,
                "population": None,
            }

    async def fetch_worldbank_health(self, country_code: str) -> Dict[str, Any]:
        life_expectancy = None
        health_expenditure = None
        gdp_per_capita = None
        try:
            life_expectancy_url = f"{self.worldbank_base_url}/{country_code}/indicator/SP.DYN.LE00.IN?format=json"
            health_expenditure_url = f"{self.worldbank_base_url}/{country_code}/indicator/SH.XPD.CHEX.GD.ZS?format=json"
            gdp_per_capita_url = f"{self.worldbank_base_url}/{country_code}/indicator/NY.GDP.PCAP.CD?format=json"

            life_expectancy_response = await self.client.get(life_expectancy_url)
            health_expenditure_response = await self.client.get(health_expenditure_url)
            gdp_per_capita_response = await self.client.get(gdp_per_capita_url)

            life_expectancy_response.raise_for_status()
            health_expenditure_response.raise_for_status()
            gdp_per_capita_response.raise_for_status()

            life_expectancy_data = life_expectancy_response.json()
            health_expenditure_data = health_expenditure_response.json()
            gdp_per_capita_data = gdp_per_capita_response.json()

            logger.debug(f"World Bank API: Life Expectancy raw response for {country_code}: {life_expectancy_data}")
            logger.debug(f"World Bank API: Health Expenditure raw response for {country_code}: {health_expenditure_data}")
            logger.debug(f"World Bank API: GDP Per Capita raw response for {country_code}: {gdp_per_capita_data}")

            if life_expectancy_data and len(life_expectancy_data) > 1 and life_expectancy_data[1]:
                for entry in life_expectancy_data[1]:
                    if entry.get("value") is not None:
                        life_expectancy = float(entry["value"])
                        break
            if life_expectancy is None:
                logger.warning(f"World Bank API: No life expectancy data found for {country_code}. Returning None.")

            if health_expenditure_data and len(health_expenditure_data) > 1 and health_expenditure_data[1]:
                for entry in health_expenditure_data[1]:
                    if entry.get("value") is not None:
                        health_expenditure = float(entry["value"])
                        break
            if health_expenditure is None:
                logger.warning(f"World Bank API: No health expenditure data found for {country_code}. Returning None.")
            
            if gdp_per_capita_data and len(gdp_per_capita_data) > 1 and gdp_per_capita_data[1]:
                for entry in gdp_per_capita_data[1]:
                    if entry.get("value") is not None:
                        gdp_per_capita = float(entry["value"])
                        break
            if gdp_per_capita is None:
                logger.warning(f"World Bank API: No GDP per capita data found for {country_code}. Returning None.")

        except httpx.HTTPStatusError as e:
            logger.error(f"World Bank API: HTTP error for {country_code}: {e}. Response: {e.response.text}. Returning None for metrics.")
        except httpx.RequestError as e:
            logger.error(f"World Bank API: Request error for {country_code}: {e}. Returning None for metrics.")
        except Exception as e:
            logger.error(f"World Bank API: An unexpected error occurred for {country_code}: {e}. Returning None for metrics.")
        
        return {
            "life_expectancy": life_expectancy,
            "health_expenditure": health_expenditure,
            "gdp_per_capita": gdp_per_capita
        }

    async def fetch_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        temperature = None
        try:
            url = f"{self.open_meteo_weather_base_url}?latitude={lat}&longitude={lon}&current_weather=true"
            logger.debug(f"Open-Meteo Weather API: Requesting URL: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Open-Meteo Weather API: Raw response for lat={lat}, lon={lon}: {data}")

            current_weather = data.get("current_weather", {})
            if current_weather.get("temperature") is not None:
                temperature = float(current_weather["temperature"])
            else:
                logger.warning(f"Open-Meteo Weather API: No temperature data found for lat={lat}, lon={lon}. Returning None.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Open-Meteo Weather API: HTTP error for lat={lat}, lon={lon}: {e}. Response: {e.response.text}. Returning None for temperature.")
        except httpx.RequestError as e:
            logger.error(f"Open-Meteo Weather API: Request error for lat={lat}, lon={lon}: {e}. Returning None for temperature.")
        except Exception as e:
            logger.error(f"Open-Meteo Weather API: An unexpected error occurred for lat={lat}, lon={lon}: {e}. Returning None for temperature.")
        
        return {
            "temperature": temperature
        }

    async def fetch_aqi(self, lat: float, lon: float) -> Dict[str, Any]:
        aqi = None
        try:
            url = f"{self.open_meteo_aqi_base_url}?latitude={lat}&longitude={lon}&hourly=us_aqi"
            logger.debug(f"Open-Meteo AQI API: Requesting URL: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Open-Meteo AQI API: Raw response for lat={lat}, lon={lon}: {data}")

            hourly_data = data.get("hourly", {})
            us_aqi_values = hourly_data.get("us_aqi")
            
            if us_aqi_values and len(us_aqi_values) > 0 and us_aqi_values[-1] is not None:
                aqi = float(us_aqi_values[-1])
            else:
                logger.warning(f"Open-Meteo AQI API: No US AQI data found for lat={lat}, lon={lon}. Returning None.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Open-Meteo AQI API: HTTP error for lat={lat}, lon={lon}: {e}. Response: {e.response.text}. Returning None for AQI.")
        except httpx.RequestError as e:
            logger.error(f"Open-Meteo AQI API: Request error for lat={lat}, lon={lon}: {e}. Returning None for AQI.")
        except Exception as e:
            logger.error(f"Open-Meteo AQI API: An unexpected error occurred for lat={lat}, lon={lon}: {e}. Returning None for AQI.")
        
        return {
            "aqi": aqi
        }

    async def fetch_travel_advisory(self, country_name: str) -> Dict[str, Any]:
        advisory_score = None
        try:
            url = self.travel_advisory_base_url
            logger.debug(f"Travel Advisory RSS: Requesting URL: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            xml_data = response.text
            logger.debug(f"Travel Advisory RSS: Raw XML response for {country_name}: {xml_data[:500]}...") # Log first 500 chars

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)

            # RSS feeds typically have items under channel/item
            for item in root.findall(".//item"):
                title_element = item.find("title")
                category_elements = item.findall("category")

                if title_element is not None and title_element.text and country_name.lower() in title_element.text.lower():
                    for category in category_elements:
                        if category.get("domain") == "Threat-Level" and category.text:
                            # Extract level number from "Level X: ..."
                            level_str = category.text.split(":")[0].strip()
                            if "Level" in level_str:
                                try:
                                    level = int(level_str.split(" ")[1])
                                    # Convert 1-4 level to 0-100 risk score (1=low risk, 4=high risk)
                                    # Level 1 -> 25, Level 2 -> 50, Level 3 -> 75, Level 4 -> 100
                                    advisory_score = (level / 4.0) * 100.0
                                    logger.debug(f"Travel Advisory RSS: Found level {level} for {country_name}, score: {advisory_score}")
                                    break # Found the score, exit category loop
                                except ValueError:
                                    logger.warning(f"Travel Advisory RSS: Could not parse level from '{category.text}' for {country_name}.")
                    if advisory_score is not None:
                        break # Found the country and score, exit item loop

            if advisory_score is None:
                logger.warning(f"Travel Advisory RSS: No advisory score found for {country_name}. Returning None.")

        except httpx.HTTPStatusError as e:
            logger.error(f"Travel Advisory RSS: HTTP error for {country_name}: {e}. Response: {e.response.text}. Returning None for advisory score.")
        except httpx.RequestError as e:
            logger.error(f"Travel Advisory RSS: Request error for {country_name}: {e}. Returning None for advisory score.")
        except ET.ParseError as e:
            logger.error(f"Travel Advisory RSS: XML parsing error for {country_name}: {e}. Returning None for advisory score.")
        except Exception as e:
            logger.error(f"Travel Advisory RSS: An unexpected error occurred for {country_name}: {e}. Returning None for advisory score.")
        
        return {
            "advisory_score": advisory_score
        }