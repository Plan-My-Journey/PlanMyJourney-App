from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.security import CurrentUser
from app.schemas.utility import (
    GeocodeAutocompleteResponse,
    GeocodeSearchResponse,
    HotelResponse,
    PlacesResponse,
    RoutingResponse,
    WeatherResponse,
)
from app.services.external_apis import UtilityApiService

router = APIRouter(tags=["utility"])
utility_service = UtilityApiService()


@router.get("/weather/{city}", response_model=WeatherResponse)
async def weather(
    city: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await utility_service.weather(city)


@router.get("/hotels/{city}", response_model=HotelResponse)
async def hotels(
    city: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await utility_service.hotels(city)


@router.get("/places/{city}", response_model=PlacesResponse)
async def places(
    city: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await utility_service.places(city)


@router.get("/geocode/autocomplete", response_model=GeocodeAutocompleteResponse)
async def geocode_autocomplete(
    text: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = 5,
):
    return await utility_service.geocode_autocomplete(text, limit=limit)


@router.get("/geocode/search", response_model=GeocodeSearchResponse)
async def geocode_search(
    text: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await utility_service.geocode_search(text)


@router.get("/routing", response_model=RoutingResponse)
async def routing(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    mode: str = "drive",
):
    return await utility_service.routing(origin_lat, origin_lon, destination_lat, destination_lon, mode=mode)
