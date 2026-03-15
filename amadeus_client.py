"""
SerpApi — Google Flights client for flight search.

Docs:    https://serpapi.com/google-flights-api
Sign up: https://serpapi.com/users/sign_up  (free, instant — 250 searches/month)

No OAuth — just a single api_key query parameter.
Free plan: 250 searches/month.

⚠️  Round-trip note: Google Flights requires TWO requests for round-trips:
    1. First request returns outbound flights + a `departure_token` per itinerary
    2. Second request uses that token to fetch matching return flights + total price
    This client handles both calls transparently.
"""

import os
import httpx
from typing import Optional
from datetime import date
from models import FlightOffer, Itinerary, Segment


SERPAPI_URL = "https://serpapi.com/search"

CABIN_CLASS_MAP = {
    "economy": "1",
    "premium_economy": "2",
    "business": "3",
    "first": "4",
}

STOPS_MAP = {
    0: "1",  # nonstop only
    1: "2",  # 1 stop or fewer
    2: "3",  # 2 stops or fewer
}


class SerpAPIAuthError(Exception):
    pass


class SerpAPISearchError(Exception):
    pass


# Keep legacy names so main.py and cli.py require zero changes
AmadeusAuthError = SerpAPIAuthError
AmadeusSearchError = SerpAPISearchError


class AmadeusClient:
    """
    Drop-in replacement backed by SerpApi's Google Flights API.
    The public interface (search_flights) is identical to previous versions.
    """

    def __init__(self, api_key: Optional[str] = None, **_kwargs):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise SerpAPIAuthError(
                "SerpApi key not found.\n"
                "1. Sign up free at https://serpapi.com/users/sign_up\n"
                "2. Copy your API key from the dashboard\n"
                "3. Add SERPAPI_KEY=your_key to your .env file\n"
                "Free plan: 250 searches/month"
            )

    def _base_params(self, currency: str, adults: int, cabin: str) -> dict:
        return {
            "engine": "google_flights",
            "api_key": self.api_key,
            "currency": currency,
            "adults": adults,
            "hl": "en",
            "travel_class": CABIN_CLASS_MAP.get(cabin.lower(), "1"),
        }

    async def _get(self, params: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(SERPAPI_URL, params=params, timeout=20.0)

        if resp.status_code == 401:
            raise SerpAPIAuthError("Invalid SerpApi key. Check your SERPAPI_KEY.")
        if resp.status_code == 429:
            raise SerpAPISearchError(
                "Rate limit reached. Free plan allows 250 searches/month. "
                "Upgrade at https://serpapi.com/pricing"
            )
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            raise SerpAPISearchError(
                body.get("error", f"Search failed ({resp.status_code}): {resp.text[:200]}")
            )

        data = resp.json()
        if "error" in data:
            raise SerpAPISearchError(data["error"])
        return data

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        adults: int = 1,
        currency: str = "USD",
        cabin_class: str = "Economy",
        max_results: int = 20,
    ) -> list[FlightOffer]:
        """Search for flight offers via SerpApi Google Flights."""

        if return_date:
            return await self._search_roundtrip(
                origin, destination, departure_date, return_date,
                adults, currency, cabin_class, max_results
            )
        else:
            return await self._search_oneway(
                origin, destination, departure_date,
                adults, currency, cabin_class, max_results
            )

    async def _search_oneway(
        self, origin, destination, departure_date, adults, currency, cabin_class, max_results
    ) -> list[FlightOffer]:
        params = self._base_params(currency, adults, cabin_class)
        params.update({
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.isoformat(),
            "type": "2",  # one-way
        })

        data = await self._get(params)
        raw_flights = data.get("best_flights", []) + data.get("other_flights", [])
        return self._parse_oneway_offers(raw_flights[:max_results], currency, cabin_class)

    async def _search_roundtrip(
        self, origin, destination, departure_date, return_date,
        adults, currency, cabin_class, max_results
    ) -> list[FlightOffer]:
        """
        Round-trip requires two API calls:
          1. Get outbound options (each has a departure_token)
          2. For the cheapest outbound, fetch return options using that token
        We pick the top N outbound flights and pair each with the cheapest return.
        """
        # Step 1: outbound flights
        params = self._base_params(currency, adults, cabin_class)
        params.update({
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.isoformat(),
            "return_date": return_date.isoformat(),
            "type": "1",  # round trip
        })
        data = await self._get(params)
        outbound_raw = (data.get("best_flights", []) + data.get("other_flights", []))[:max_results]

        if not outbound_raw:
            return []

        # Step 2: for the first (cheapest/best) outbound, fetch return leg
        # to get combined pricing. We use the first departure_token available.
        offers = []
        departure_token = None
        for flight in outbound_raw:
            if flight.get("departure_token"):
                departure_token = flight["departure_token"]
                break

        return_flights_by_price: dict = {}
        if departure_token:
            ret_params = self._base_params(currency, adults, cabin_class)
            ret_params.update({
                "departure_id": origin.upper(),
                "arrival_id": destination.upper(),
                "outbound_date": departure_date.isoformat(),
                "return_date": return_date.isoformat(),
                "type": "1",
                "departure_token": departure_token,
            })
            try:
                ret_data = await self._get(ret_params)
                return_raw = ret_data.get("best_flights", []) + ret_data.get("other_flights", [])
                # Map return flights by price for pairing
                for r in return_raw:
                    price = r.get("price")
                    if price and price not in return_flights_by_price:
                        return_flights_by_price[price] = r
            except SerpAPISearchError:
                pass  # Fall back to one-way style offers if return fetch fails

        for idx, outbound in enumerate(outbound_raw):
            try:
                outbound_itin = self._parse_leg(outbound.get("flights", []), cabin_class)
                if not outbound_itin:
                    continue

                itineraries = [outbound_itin]
                price = float(outbound.get("price", 0))

                # Attach cheapest return leg if available
                if return_flights_by_price:
                    cheapest_return = min(return_flights_by_price.keys())
                    return_itin = self._parse_leg(
                        return_flights_by_price[cheapest_return].get("flights", []), cabin_class
                    )
                    if return_itin:
                        itineraries.append(return_itin)
                        price = float(cheapest_return)  # combined price from return call

                offers.append(FlightOffer(
                    id=str(idx),
                    price=price,
                    currency=currency,
                    itineraries=itineraries,
                    seats_available=None,
                    cabin_class=cabin_class.upper(),
                    is_refundable=None,
                ))
            except (KeyError, ValueError, TypeError):
                continue

        return offers

    def _parse_leg(self, flights_raw: list, cabin_class: str) -> Optional[Itinerary]:
        """Parse a list of flight segments into an Itinerary."""
        if not flights_raw:
            return None

        segments = []
        total_mins = 0
        for seg in flights_raw:
            dep = seg.get("departure_airport", {})
            arr = seg.get("arrival_airport", {})
            duration_mins = seg.get("duration", 0)
            total_mins += duration_mins
            segments.append(Segment(
                departure_airport=dep.get("id", ""),
                arrival_airport=arr.get("id", ""),
                departure_time=dep.get("time", ""),
                arrival_time=arr.get("time", ""),
                carrier=seg.get("airline", ""),
                flight_number=seg.get("flight_number", ""),
                duration=self._fmt_duration(duration_mins),
            ))

        return Itinerary(
            segments=segments,
            total_duration=self._fmt_duration(total_mins),
            stops=max(len(segments) - 1, 0),
        )

    def _parse_oneway_offers(
        self, raw_flights: list, currency: str, cabin_class: str
    ) -> list[FlightOffer]:
        offers = []
        for idx, raw in enumerate(raw_flights):
            try:
                itin = self._parse_leg(raw.get("flights", []), cabin_class)
                if not itin:
                    continue
                offers.append(FlightOffer(
                    id=str(idx),
                    price=float(raw.get("price", 0)),
                    currency=currency,
                    itineraries=[itin],
                    seats_available=None,
                    cabin_class=cabin_class.upper(),
                    is_refundable=None,
                ))
            except (KeyError, ValueError, TypeError):
                continue
        return offers

    def _fmt_duration(self, minutes: int) -> str:
        h, m = divmod(minutes, 60)
        parts = []
        if h:
            parts.append(f"{h}h")
        if m:
            parts.append(f"{m}m")
        return " ".join(parts) or "0m"


class SerpAPIClient(AmadeusClient):
    """Explicit alias — use this name in new code."""
    pass