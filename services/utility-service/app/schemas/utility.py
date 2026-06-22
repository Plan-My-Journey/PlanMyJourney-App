from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    city: str
    temperature_c: float
    feels_like_c: float
    humidity: int
    condition: str
    wind_speed_mps: float
    source: str


class HotelRecommendation(BaseModel):
    name: str
    address: str
    rating: float | None = None
    price_level: int | None = Field(default=None, ge=0, le=4)
    open_now: bool | None = None


class HotelResponse(BaseModel):
    city: str
    hotels: list[HotelRecommendation]
    source: str


class PlaceRecommendation(BaseModel):
    name: str
    address: str
    rating: float | None = None
    categories: list[str] = Field(default_factory=list)
    place_id: str | None = None


class PlacesResponse(BaseModel):
    city: str
    places: list[PlaceRecommendation]
    source: str
