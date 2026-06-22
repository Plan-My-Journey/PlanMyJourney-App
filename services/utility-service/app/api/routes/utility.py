from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.security import CurrentUser
from app.schemas.utility import HotelResponse, PlacesResponse, WeatherResponse
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
