import hashlib
from typing import Any

import httpx

from app.core.config import settings


class UtilityApiService:
    async def weather(self, city: str) -> dict[str, Any]:
        if not settings.openweather_api_key:
            return self._fallback_weather(city)

        params = {
            "q": city,
            "appid": settings.openweather_api_key,
            "units": "metric",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
                response.raise_for_status()
            data = response.json()
            condition = data.get("weather", [{}])[0].get("description", "Unavailable")
            main = data.get("main", {})
            wind = data.get("wind", {})
            return {
                "city": data.get("name", city),
                "temperature_c": float(main.get("temp", 0)),
                "feels_like_c": float(main.get("feels_like", main.get("temp", 0))),
                "humidity": int(main.get("humidity", 0)),
                "condition": condition.title(),
                "wind_speed_mps": float(wind.get("speed", 0)),
                "source": "openweathermap",
            }
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return self._fallback_weather(city)

    async def hotels(self, city: str) -> dict[str, Any]:
        if settings.geoapify_api_key:
            geoapify_hotels = await self._geoapify_places(
                city,
                "accommodation.hotel,accommodation.hostel,accommodation.guest_house",
                limit=8,
            )
            if geoapify_hotels is not None:
                return {"city": city, "hotels": geoapify_hotels, "source": "geoapify"}

        if not settings.google_maps_api_key:
            return self._fallback_hotels(city)
        data = await self._google_text_search(f"hotels in {city}", "lodging")
        if data is None:
            return self._fallback_hotels(city)

        hotels = []
        for item in data.get("results", [])[:8]:
            hotels.append(
                {
                    "name": item.get("name", "Hotel"),
                    "address": item.get("formatted_address", "Address unavailable"),
                    "rating": item.get("rating"),
                    "price_level": item.get("price_level"),
                    "open_now": item.get("opening_hours", {}).get("open_now"),
                }
            )
        return {"city": city, "hotels": hotels, "source": "google_places"}

    async def places(self, city: str) -> dict[str, Any]:
        if settings.geoapify_api_key:
            geoapify_places = await self._geoapify_places(
                city,
                "tourism.sights,tourism.attraction,entertainment.museum,catering.restaurant,natural",
                limit=10,
            )
            if geoapify_places is not None:
                return {"city": city, "places": geoapify_places, "source": "geoapify"}

        if not settings.google_maps_api_key:
            return self._fallback_places(city)
        data = await self._google_text_search(f"top tourist attractions in {city}", "tourist_attraction")
        if data is None:
            return self._fallback_places(city)

        places = []
        for item in data.get("results", [])[:10]:
            places.append(
                {
                    "name": item.get("name", "Place"),
                    "address": item.get("formatted_address", "Address unavailable"),
                    "rating": item.get("rating"),
                    "categories": item.get("types", [])[:4],
                    "place_id": item.get("place_id"),
                }
            )
        return {"city": city, "places": places, "source": "google_places"}

    async def _geoapify_places(self, city: str, categories: str, limit: int) -> list[dict[str, Any]] | None:
        coordinates = await self._geoapify_city_coordinates(city)
        if coordinates is None:
            return None

        latitude, longitude = coordinates
        params = {
            "categories": categories,
            "filter": f"circle:{longitude},{latitude},12000",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": limit,
            "apiKey": settings.geoapify_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get("https://api.geoapify.com/v2/places", params=params)
                response.raise_for_status()
            features = response.json().get("features", [])
            results = []
            for feature in features:
                properties = feature.get("properties", {})
                name = properties.get("name") or properties.get("address_line1")
                if not name:
                    continue
                categories_value = properties.get("categories", [])
                result = {
                    "name": name,
                    "address": properties.get("formatted") or properties.get("address_line2") or city,
                    "rating": None,
                    "categories": categories_value[:4] if isinstance(categories_value, list) else [],
                    "place_id": properties.get("place_id"),
                }
                if "accommodation" in categories:
                    result = {
                        "name": name,
                        "address": result["address"],
                        "rating": None,
                        "price_level": None,
                        "open_now": None,
                    }
                results.append(result)
            return results
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return None

    async def _geoapify_city_coordinates(self, city: str) -> tuple[float, float] | None:
        params = {
            "text": city,
            "limit": 1,
            "apiKey": settings.geoapify_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get("https://api.geoapify.com/v1/geocode/search", params=params)
                response.raise_for_status()
            features = response.json().get("features", [])
            if not features:
                return None
            properties = features[0].get("properties", {})
            return float(properties["lat"]), float(properties["lon"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            return None

    async def _google_text_search(self, query: str, place_type: str) -> dict[str, Any] | None:
        params = {
            "query": query,
            "type": place_type,
            "key": settings.google_maps_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params)
                response.raise_for_status()
            data = response.json()
            if data.get("status") not in {"OK", "ZERO_RESULTS"}:
                return None
            return data
        except (httpx.HTTPError, ValueError):
            return None

    @staticmethod
    def _fallback_weather(city: str) -> dict[str, Any]:
        seed = int(hashlib.sha256(city.lower().encode("utf-8")).hexdigest(), 16)
        temperature = 18 + seed % 14
        humidity = 45 + seed % 40
        conditions = ["Clear", "Partly Cloudy", "Light Rain", "Warm", "Breezy"]
        return {
            "city": city.title(),
            "temperature_c": float(temperature),
            "feels_like_c": float(temperature + (seed % 3) - 1),
            "humidity": int(humidity),
            "condition": conditions[seed % len(conditions)],
            "wind_speed_mps": float(2 + seed % 6),
            "source": "local_fallback",
        }

    @staticmethod
    def _fallback_hotels(city: str) -> dict[str, Any]:
        return {
            "city": city,
            "hotels": [
                {"name": f"{city.title()} Central Stay", "address": f"Central district, {city.title()}", "rating": 4.4, "price_level": 3, "open_now": True},
                {"name": f"{city.title()} Heritage Inn", "address": f"Old town, {city.title()}", "rating": 4.2, "price_level": 2, "open_now": True},
                {"name": f"{city.title()} Transit Hotel", "address": f"Station area, {city.title()}", "rating": 4.0, "price_level": 2, "open_now": None},
            ],
            "source": "local_fallback",
        }

    @staticmethod
    def _fallback_places(city: str) -> dict[str, Any]:
        return {
            "city": city,
            "places": [
                {"name": f"{city.title()} Historic Quarter", "address": f"Old city, {city.title()}", "rating": 4.6, "categories": ["walking", "history"], "place_id": None},
                {"name": f"{city.title()} Food Market", "address": f"Market district, {city.title()}", "rating": 4.5, "categories": ["food", "local_culture"], "place_id": None},
                {"name": f"{city.title()} Viewpoint", "address": f"Scenic area, {city.title()}", "rating": 4.4, "categories": ["outdoors", "photography"], "place_id": None},
            ],
            "source": "local_fallback",
        }
