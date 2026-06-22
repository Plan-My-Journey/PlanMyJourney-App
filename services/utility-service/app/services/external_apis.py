import hashlib
from typing import Any

import httpx

from app.core.config import settings

GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_AUTOCOMPLETE_URL = "https://api.geoapify.com/v1/geocode/autocomplete"
GEOAPIFY_ROUTING_URL = "https://api.geoapify.com/v1/routing"
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"


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

        return self._fallback_hotels(city)

    async def places(self, city: str) -> dict[str, Any]:
        if settings.geoapify_api_key:
            geoapify_places = await self._geoapify_places(
                city,
                "tourism.sights,tourism.attraction,entertainment.museum,catering.restaurant,natural",
                limit=10,
            )
            if geoapify_places is not None:
                return {"city": city, "places": geoapify_places, "source": "geoapify"}

        return self._fallback_places(city)

    async def geocode_autocomplete(self, text: str, limit: int = 5) -> dict[str, Any]:
        query = text.strip()
        if len(query) < 3:
            return {"query": query, "suggestions": [], "source": "local_fallback"}

        if not settings.geoapify_api_key:
            return {"query": query, "suggestions": self._fallback_autocomplete(query), "source": "local_fallback"}

        params = {
            "text": query,
            "limit": min(max(limit, 1), 8),
            "apiKey": settings.geoapify_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(GEOAPIFY_AUTOCOMPLETE_URL, params=params)
                response.raise_for_status()
            suggestions = []
            for feature in response.json().get("features", []):
                properties = feature.get("properties", {})
                label = properties.get("formatted") or properties.get("address_line1")
                if not label:
                    continue
                suggestions.append(
                    {
                        "label": label,
                        "city": properties.get("city") or properties.get("name") or label,
                        "country": properties.get("country"),
                        "latitude": properties.get("lat"),
                        "longitude": properties.get("lon"),
                        "place_id": properties.get("place_id"),
                    }
                )
            return {"query": query, "suggestions": suggestions, "source": "geoapify"}
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return {"query": query, "suggestions": self._fallback_autocomplete(query), "source": "local_fallback"}

    async def geocode_search(self, text: str) -> dict[str, Any]:
        query = text.strip()
        if not query:
            return {"query": query, "results": [], "source": "local_fallback"}

        if not settings.geoapify_api_key:
            return {"query": query, "results": [], "source": "local_fallback"}

        params = {"text": query, "limit": 1, "apiKey": settings.geoapify_api_key}
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(GEOAPIFY_GEOCODE_URL, params=params)
                response.raise_for_status()
            results = []
            for feature in response.json().get("features", []):
                properties = feature.get("properties", {})
                results.append(
                    {
                        "label": properties.get("formatted") or query,
                        "city": properties.get("city") or properties.get("name") or query,
                        "country": properties.get("country"),
                        "latitude": properties.get("lat"),
                        "longitude": properties.get("lon"),
                        "place_id": properties.get("place_id"),
                    }
                )
            return {"query": query, "results": results, "source": "geoapify"}
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return {"query": query, "results": [], "source": "local_fallback"}

    async def routing(
        self,
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
        mode: str = "drive",
    ) -> dict[str, Any]:
        allowed_modes = {"drive", "walk", "bicycle", "transit"}
        travel_mode = mode if mode in allowed_modes else "drive"

        if not settings.geoapify_api_key:
            return self._fallback_routing(origin_lat, origin_lon, destination_lat, destination_lon, travel_mode)

        params = {
            "waypoints": f"{origin_lat},{origin_lon}|{destination_lat},{destination_lon}",
            "mode": travel_mode,
            "apiKey": settings.geoapify_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.get(GEOAPIFY_ROUTING_URL, params=params)
                response.raise_for_status()
            features = response.json().get("features", [])
            if not features:
                return self._fallback_routing(origin_lat, origin_lon, destination_lat, destination_lon, travel_mode)

            properties = features[0].get("properties", {})
            return {
                "mode": travel_mode,
                "distance_meters": properties.get("distance"),
                "duration_seconds": properties.get("time"),
                "origin": {"latitude": origin_lat, "longitude": origin_lon},
                "destination": {"latitude": destination_lat, "longitude": destination_lon},
                "source": "geoapify",
            }
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return self._fallback_routing(origin_lat, origin_lon, destination_lat, destination_lon, travel_mode)

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
                response = await client.get(GEOAPIFY_PLACES_URL, params=params)
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
                response = await client.get(GEOAPIFY_GEOCODE_URL, params=params)
                response.raise_for_status()
            features = response.json().get("features", [])
            if not features:
                return None
            properties = features[0].get("properties", {})
            return float(properties["lat"]), float(properties["lon"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
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

    @staticmethod
    def _fallback_autocomplete(query: str) -> list[dict[str, Any]]:
        return [{"label": query.title(), "city": query.title(), "country": None, "latitude": None, "longitude": None, "place_id": None}]

    @staticmethod
    def _fallback_routing(
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
        mode: str,
    ) -> dict[str, Any]:
        distance = ((destination_lat - origin_lat) ** 2 + (destination_lon - origin_lon) ** 2) ** 0.5 * 111_000
        speed_mps = 1.4 if mode == "walk" else 13.9
        return {
            "mode": mode,
            "distance_meters": round(distance),
            "duration_seconds": round(distance / speed_mps),
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": destination_lat, "longitude": destination_lon},
            "source": "local_fallback",
        }
