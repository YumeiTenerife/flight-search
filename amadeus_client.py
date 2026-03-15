"""
SerpApi — Google Flights client for flight search.

Docs:    https://serpapi.com/google-flights-api
Sign up: https://serpapi.com/users/sign_up  (free, instant — 250 searches/month)

No OAuth — just a single api_key query parameter.
Free plan: 250 searches/month.

Round-trip note: Google Flights requires TWO requests for round-trips:
    1. First request returns outbound flights + a departure_token per itinerary
    2. Second request uses that token to fetch matching return flights + total price
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

    def _base_params(self, currency: str, adults: int, cabin: str,
                     carry_on_bags: int = 0, checked_bags: int = 0) -> dict:
        params = {
            "engine": "google_flights",
            "api_key": self.api_key,
            "currency": currency,
            "adults": adults,
            "hl": "en",
            "travel_class": CABIN_CLASS_MAP.get(cabin.lower(), "1"),
        }
        if carry_on_bags > 0:
            params["carry_on_bags"] = min(carry_on_bags, adults)
        if checked_bags > 0:
            params["checked_bags"] = min(checked_bags, adults)
        return params

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
            body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
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
        carry_on_bags: int = 0,
        checked_bags: int = 0,
        max_results: int = 20,
    ) -> list[FlightOffer]:
        if return_date:
            return await self._search_roundtrip(
                origin, destination, departure_date, return_date,
                adults, currency, cabin_class, carry_on_bags, checked_bags, max_results
            )
        else:
            return await self._search_oneway(
                origin, destination, departure_date,
                adults, currency, cabin_class, carry_on_bags, checked_bags, max_results
            )

    async def _search_oneway(
        self, origin, destination, departure_date, adults, currency, cabin_class,
        carry_on_bags, checked_bags, max_results
    ) -> list[FlightOffer]:
        params = self._base_params(currency, adults, cabin_class, carry_on_bags, checked_bags)
        params.update({
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.isoformat(),
            "type": "2",
        })
        data = await self._get(params)
        raw_flights = data.get("best_flights", []) + data.get("other_flights", [])
        return self._parse_oneway_offers(raw_flights[:max_results], currency, cabin_class)

    async def _search_roundtrip(
        self, origin, destination, departure_date, return_date,
        adults, currency, cabin_class, carry_on_bags, checked_bags, max_results
    ) -> list[FlightOffer]:
        params = self._base_params(currency, adults, cabin_class, carry_on_bags, checked_bags)
        params.update({
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.isoformat(),
            "return_date": return_date.isoformat(),
            "type": "1",
        })
        data = await self._get(params)
        outbound_raw = (data.get("best_flights", []) + data.get("other_flights", []))[:max_results]

        if not outbound_raw:
            return []

        departure_token = next(
            (f["departure_token"] for f in outbound_raw if f.get("departure_token")), None
        )

        return_flights_by_price = {}
        if departure_token:
            ret_params = self._base_params(currency, adults, cabin_class, carry_on_bags, checked_bags)
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
                for r in ret_data.get("best_flights", []) + ret_data.get("other_flights", []):
                    price = r.get("price")
                    if price and price not in return_flights_by_price:
                        return_flights_by_price[price] = r
            except SerpAPISearchError:
                pass

        offers = []
        for idx, outbound in enumerate(outbound_raw):
            try:
                outbound_itin = self._parse_leg(outbound.get("flights", []))
                if not outbound_itin:
                    continue

                itineraries = [outbound_itin]
                price = float(outbound.get("price", 0))
                booking_url, booking_agent = self._extract_booking(outbound)

                if return_flights_by_price:
                    cheapest_return = min(return_flights_by_price.keys())
                    return_raw = return_flights_by_price[cheapest_return]
                    return_itin = self._parse_leg(return_raw.get("flights", []))
                    if return_itin:
                        itineraries.append(return_itin)
                        price = float(cheapest_return)
                        if not booking_url:
                            booking_url, booking_agent = self._extract_booking(return_raw)

                offers.append(FlightOffer(
                    id=str(idx),
                    price=price,
                    currency=currency,
                    itineraries=itineraries,
                    seats_available=None,
                    cabin_class=cabin_class.upper(),
                    is_refundable=None,
                    booking_url=booking_url,
                    booking_agent=booking_agent,
                ))
            except (KeyError, ValueError, TypeError):
                continue

        return offers

    def _extract_booking(self, raw: dict) -> tuple:
        """
        SerpApi returns booking options in different shapes depending on the query.
        Try the most common paths in order.
        """
        # Path 1: extensions.booking_options array
        options = raw.get("extensions", {}).get("booking_options", [])
        if options:
            best = options[0]
            return best.get("book_with_carrier") or best.get("url"), best.get("book_with")

        # Path 2: top-level booking_options
        options = raw.get("booking_options", [])
        if options:
            best = options[0]
            return best.get("book_with_carrier") or best.get("url"), best.get("book_with")

        # Path 3: direct url field
        return raw.get("url"), None

    def _parse_leg(self, flights_raw: list) -> Optional[Itinerary]:
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
                itin = self._parse_leg(raw.get("flights", []))
                if not itin:
                    continue
                booking_url, booking_agent = self._extract_booking(raw)
                offers.append(FlightOffer(
                    id=str(idx),
                    price=float(raw.get("price", 0)),
                    currency=currency,
                    itineraries=[itin],
                    seats_available=None,
                    cabin_class=cabin_class.upper(),
                    is_refundable=None,
                    booking_url=booking_url,
                    booking_agent=booking_agent,
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