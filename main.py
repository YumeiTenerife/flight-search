"""
Flight Search REST API — powered by Amadeus
Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from dotenv import load_dotenv
load_dotenv(encoding="utf-8")

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


def _parse_dt(s: str):
    from datetime import datetime
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace(" ", "T"))
    except ValueError:
        return None


def _has_overnight_layover(offer: FlightOffer) -> bool:
    """
    Returns True if any connection is 5+ hours AND spans the night window (22:00–04:00).
    """
    from datetime import timedelta
    for itin in offer.itineraries:
        segs = itin.segments
        for i in range(len(segs) - 1):
            arr = _parse_dt(segs[i].arrival_time)
            dep = _parse_dt(segs[i + 1].departure_time)
            if not arr or not dep:
                continue
            layover_mins = (dep - arr).total_seconds() / 60
            if layover_mins < 300:   # less than 5 hours — skip
                continue
            cursor = arr
            while cursor < dep:
                if cursor.hour >= 22 or cursor.hour < 4:
                    return True
                cursor += timedelta(hours=1)
    return False


def _has_avoided_country(offer: FlightOffer, avoid: set) -> bool:
    """Returns True if any layover airport is in an avoided country."""
    if not avoid:
        return False
    for itin in offer.itineraries:
        segs = itin.segments
        for seg in segs[:-1]:  # only connection airports, not final destination
            country = AIRPORT_COUNTRY.get(seg.arrival_airport.upper())
            if country and country in avoid:
                return True
    return False


# Airport IATA → ISO country code for common connection hubs
AIRPORT_COUNTRY: dict = {
    "YYZ": "CA", "YVR": "CA", "YUL": "CA", "YYC": "CA", "YOW": "CA",
    "JFK": "US", "LAX": "US", "ORD": "US", "ATL": "US", "DFW": "US",
    "MIA": "US", "SFO": "US", "SEA": "US", "BOS": "US", "EWR": "US",
    "IAD": "US", "IAH": "US", "MSP": "US", "DTW": "US", "PHL": "US",
    "MEX": "MX", "CUN": "MX",
    "LHR": "GB", "LGW": "GB", "MAN": "GB", "EDI": "GB",
    "CDG": "FR", "ORY": "FR", "NCE": "FR", "LYS": "FR",
    "AMS": "NL",
    "FRA": "DE", "MUC": "DE", "BER": "DE", "DUS": "DE", "HAM": "DE",
    "MAD": "ES", "BCN": "ES",
    "FCO": "IT", "MXP": "IT", "VCE": "IT", "NAP": "IT",
    "ZRH": "CH", "GVA": "CH",
    "VIE": "AT", "BRU": "BE", "LIS": "PT",
    "CPH": "DK", "ARN": "SE", "OSL": "NO", "HEL": "FI",
    "WAW": "PL", "PRG": "CZ", "BUD": "HU", "ATH": "GR",
    "IST": "TR", "SAW": "TR", "AYT": "TR",
    "DXB": "AE", "AUH": "AE", "SHJ": "AE",
    "DOH": "QA", "BAH": "BH", "KWI": "KW", "AMM": "JO",
    "BEY": "LB", "TLV": "IL",
    "RUH": "SA", "JED": "SA", "DMM": "SA",
    "SIN": "SG",
    "BKK": "TH", "HKT": "TH",
    "KUL": "MY", "CGK": "ID", "DPS": "ID", "MNL": "PH",
    "SGN": "VN", "HAN": "VN",
    "PEK": "CN", "PVG": "CN", "CAN": "CN", "CTU": "CN",
    "HKG": "HK", "TPE": "TW",
    "ICN": "KR", "GMP": "KR",
    "NRT": "JP", "HND": "JP", "KIX": "JP",
    "DEL": "IN", "BOM": "IN", "BLR": "IN", "MAA": "IN",
    "CMB": "LK", "DAC": "BD",
    "JNB": "ZA", "CPT": "ZA",
    "CAI": "EG", "HRG": "EG", "SSH": "EG",
    "CMN": "MA", "ADD": "ET", "NBO": "KE", "LOS": "NG",
    "SYD": "AU", "MEL": "AU", "BNE": "AU", "PER": "AU",
    "AKL": "NZ",
    "GRU": "BR", "GIG": "BR",
    "EZE": "AR", "SCL": "CL", "BOG": "CO", "LIM": "PE",
    "PTY": "PA",
}


def apply_filters(
    offers: list[FlightOffer],
    max_price: Optional[float],
    max_stops: Optional[int],
    no_overnight_layover: bool = False,
    avoid_countries: Optional[str] = None,
) -> list[FlightOffer]:
    if max_price is not None:
        offers = [o for o in offers if o.price <= max_price]
    if max_stops is not None:
        offers = [o for o in offers if all(i.stops <= max_stops for i in o.itineraries)]
    if no_overnight_layover:
        offers = [o for o in offers if not _has_overnight_layover(o)]
    if avoid_countries:
        avoid_set = {c.strip().upper() for c in avoid_countries.split(",") if c.strip()}
        offers = [o for o in offers if not _has_avoided_country(o, avoid_set)]
    return offers


@app.get("/nearby-dates", tags=["Flights"])
async def nearby_dates(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    departure_date: date = Query(...),
    currency: str = Query("USD"),
    adults: int = Query(1, ge=1, le=9),
):
    """
    Search ±3 days around the given date in parallel and return
    the cheapest price found per date.
    Uses asyncio.gather so all 7 searches run concurrently.
    """
    import asyncio
    from datetime import timedelta

    dates = [departure_date + timedelta(days=i) for i in range(-3, 4)]

    async def search_one(d: date):
        try:
            offers, _ = await amadeus.search_flights(
                origin=origin,
                destination=destination,
                departure_date=d,
                adults=adults,
                currency=currency,
                max_results=5,
            )
            if offers:
                return d.isoformat(), min(o.price for o in offers)
        except Exception:
            pass
        return d.isoformat(), None

    results = await asyncio.gather(*[search_one(d) for d in dates])

    return {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "currency": currency,
        "dates": [{"date": date_str, "price": price} for date_str, price in results],
    }


@app.get("/autocomplete", tags=["Airports"])
async def autocomplete_airports(q: str = Query(..., min_length=2, description="City or airport name")):
    """Return airport suggestions for a search query via SerpApi autocomplete."""
    import httpx
    import os
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="SERPAPI_KEY not configured.")
    if len(q) < 2:
        return {"suggestions": []}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://serpapi.com/search",
            params={"engine": "google_flights_autocomplete", "q": q, "hl": "en", "api_key": api_key},
            timeout=8.0,
        )
    if resp.status_code != 200:
        return {"suggestions": []}
    data = resp.json()
    results = []
    for suggestion in data.get("suggestions", []):
        for airport in suggestion.get("airports", []):
            results.append({
                "id": airport.get("id"),
                "name": airport.get("name"),
                "city": suggestion.get("name"),
                "country": suggestion.get("description", ""),
                "distance": airport.get("distance", ""),
            })
    return {"suggestions": results[:8]}


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
    no_overnight_layover: bool = Query(False, description="Exclude itineraries with 12+ hour overnight connections"),
    avoid_countries: Optional[str] = Query(None, description="Comma-separated ISO country codes to avoid for connections, e.g. US,TR"),
    carry_on_bags: int = Query(0, ge=0, le=9, description="Number of carry-on bags per passenger"),
    checked_bags: int = Query(0, ge=0, le=9, description="Number of checked bags per passenger"),
):
    if amadeus is None:
        raise HTTPException(
            status_code=503,
            detail="SerpApi key not configured. Set SERPAPI_KEY in your .env file.",
        )

    if return_date and return_date <= departure_date:
        raise HTTPException(status_code=400, detail="return_date must be after departure_date.")

    try:
        offers, price_insights_raw = await amadeus.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            currency=currency,
            carry_on_bags=carry_on_bags,
            checked_bags=checked_bags,
        )
    except AmadeusSearchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    offers = apply_filters(
        offers,
        max_price=max_price,
        max_stops=max_stops,
        no_overnight_layover=no_overnight_layover,
        avoid_countries=avoid_countries,
    )

    if sort_by == "price":
        offers.sort(key=lambda o: o.price)
    elif sort_by == "duration":
        offers.sort(key=lambda o: o.itineraries[0].total_duration if o.itineraries else "")
    elif sort_by == "stops":
        offers.sort(key=lambda o: o.itineraries[0].stops if o.itineraries else 99)

    from models import PriceInsights
    pi = PriceInsights(**price_insights_raw) if price_insights_raw else None

    return FlightSearchResponse(
        origin=origin.upper(),
        destination=destination.upper(),
        departure_date=departure_date.isoformat(),
        results_count=len(offers),
        currency=currency,
        offers=offers,
        price_insights=pi,
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
