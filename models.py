from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., description="IATA airport code, e.g. 'YYZ'")
    destination: str = Field(..., description="IATA airport code, e.g. 'JFK'")
    departure_date: date = Field(..., description="Date in YYYY-MM-DD format")
    return_date: Optional[date] = Field(None, description="Return date for round trips")
    adults: int = Field(1, ge=1, le=9)
    max_price: Optional[float] = Field(None, description="Maximum total price in USD")
    max_stops: Optional[int] = Field(None, ge=0, le=3, description="0 = non-stop only")
    currency: str = Field("USD", description="Currency code")


class Segment(BaseModel):
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    carrier: str
    flight_number: str
    duration: str


class Itinerary(BaseModel):
    segments: List[Segment]
    total_duration: str
    stops: int


class FlightOffer(BaseModel):
    id: str
    price: float
    currency: str
    itineraries: List[Itinerary]
    seats_available: Optional[int]
    cabin_class: str
    is_refundable: Optional[bool]
    booking_url: Optional[str] = None
    booking_agent: Optional[str] = None


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    departure_date: str
    results_count: int
    currency: str
    offers: List[FlightOffer]