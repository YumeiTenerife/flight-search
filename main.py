"""
Flight Search REST API — powered by Amadeus
Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import date

from models import FlightSearchRequest, FlightSearchResponse, FlightOffer
from amadeus_client import AmadeusClient, AmadeusAuthError, AmadeusSearchError

app = FastAPI(
    title="Flight Search API",
    description="Search for flights powered by the Amadeus API — similar to Skyscanner.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client is instantiated once and reuses its OAuth token across requests
try:
    amadeus = AmadeusClient()
except AmadeusAuthError as e:
    print(f"\n⚠️  WARNING: {e}\n")
    amadeus = None


def apply_filters(
    offers: list[FlightOffer],
    max_price: Optional[float],
    max_stops: Optional[int],
) -> list[FlightOffer]:
    """Filter flight offers by price and/or number of stops."""
    if max_price is not None:
        offers = [o for o in offers if o.price <= max_price]
    if max_stops is not None:
        offers = [
            o for o in offers
            if all(itin.stops <= max_stops for itin in o.itineraries)
        ]
    return offers


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Flight Search API is running. Visit /docs for the API reference."}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "amadeus_configured": amadeus is not None}


@app.get("/search", response_model=FlightSearchResponse, tags=["Flights"])
async def search_flights(
    origin: str = Query(..., description="Origin IATA code (e.g. YYZ, JFK, LHR)", min_length=3, max_length=3),
    destination: str = Query(..., description="Destination IATA code (e.g. CDG, DXB, NRT)", min_length=3, max_length=3),
    departure_date: date = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[date] = Query(None, description="Return date for round-trips (YYYY-MM-DD)"),
    adults: int = Query(1, ge=1, le=9, description="Number of adult passengers"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum total price"),
    max_stops: Optional[int] = Query(None, ge=0, le=3, description="Max stops (0 = non-stop only)"),
    currency: str = Query("USD", description="Currency code (USD, EUR, CAD, etc.)"),
    sort_by: str = Query("price", description="Sort results by: price | duration | stops"),
):
    if amadeus is None:
        raise HTTPException(
            status_code=503,
            detail="Amadeus API credentials not configured. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET.",
        )

    if return_date and return_date <= departure_date:
        raise HTTPException(status_code=400, detail="return_date must be after departure_date.")

    try:
        offers = await amadeus.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            currency=currency,
        )
    except AmadeusSearchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    # Apply filters
    offers = apply_filters(offers, max_price=max_price, max_stops=max_stops)

    # Sort results
    if sort_by == "price":
        offers.sort(key=lambda o: o.price)
    elif sort_by == "duration":
        offers.sort(key=lambda o: o.itineraries[0].total_duration if o.itineraries else "")
    elif sort_by == "stops":
        offers.sort(key=lambda o: o.itineraries[0].stops if o.itineraries else 99)

    return FlightSearchResponse(
        origin=origin.upper(),
        destination=destination.upper(),
        departure_date=departure_date.isoformat(),
        results_count=len(offers),
        currency=currency,
        offers=offers,
    )


@app.post("/search", response_model=FlightSearchResponse, tags=["Flights"])
async def search_flights_post(request: FlightSearchRequest):
    """POST version for structured JSON requests."""
    return await search_flights(
        origin=request.origin,
        destination=request.destination,
        departure_date=request.departure_date,
        return_date=request.return_date,
        adults=request.adults,
        max_price=request.max_price,
        max_stops=request.max_stops,
        currency=request.currency,
        sort_by="price",
    )