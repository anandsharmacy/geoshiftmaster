from cachetools import TTLCache
from typing import Dict, Any

country_cache = TTLCache(maxsize=100, ttl=3600)
in_flight_requests: Dict[str, Any] = {}

def get_cached(country_code: str):
    return country_cache.get(country_code)

def set_cache(country_code: str, data: Dict[str, Any]):
    if data is not None:
        country_cache[country_code] = data

def is_in_flight(country_code: str):
    return country_code in in_flight_requests

def get_in_flight(country_code: str):
    return in_flight_requests.get(country_code)

def set_in_flight(country_code: str, task):
    in_flight_requests[country_code] = task

def remove_in_flight(country_code: str):
    if country_code in in_flight_requests:
        del in_flight_requests[country_code]