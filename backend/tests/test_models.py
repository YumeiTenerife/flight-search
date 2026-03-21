"""
Unit tests for Pydantic models.
"""

import pytest
from datetime import date
from pydantic import ValidationError
from models import (
    FlightSearchRequest, FlightOffer, Itinerary, Segment,
    PriceInsights, FlightSearchResponse
)


class TestFlightSearchRequest:
    """Test FlightSearchRequest model validation."""

    def test_valid_request(self, sample_flight_search_request):
        """Test creating a valid flight search request."""
        assert sample_flight_search_request.origin == "YYZ"
        assert sample_flight_search_request.destination == "JFK"
        assert sample_flight_search_request.adults == 2
        assert sample_flight_search_request.currency == "USD"

    def test_minimal_request(self):
        """Test creating request with minimal fields."""
        req = FlightSearchRequest(
            origin="LAX",
            destination="FRA",
            departure_date=date(2024, 7, 1)
        )
        assert req.adults == 1
        assert req.currency == "USD"
        assert req.return_date is None

    def test_invalid_adults_zero(self):
        """Test that adults=0 is invalid."""
        with pytest.raises(ValidationError):
            FlightSearchRequest(
                origin="YYZ",
                destination="JFK",
                departure_date=date(2024, 6, 15),
                adults=0
            )

    def test_invalid_adults_too_many(self):
        """Test that adults>9 is invalid."""
        with pytest.raises(ValidationError):
            FlightSearchRequest(
                origin="YYZ",
                destination="JFK",
                departure_date=date(2024, 6, 15),
                adults=10
            )

    def test_invalid_max_stops_negative(self):
        """Test that negative max_stops is invalid."""
        with pytest.raises(ValidationError):
            FlightSearchRequest(
                origin="YYZ",
                destination="JFK",
                departure_date=date(2024, 6, 15),
                max_stops=-1
            )

    def test_invalid_max_stops_too_high(self):
        """Test that max_stops>3 is invalid."""
        with pytest.raises(ValidationError):
            FlightSearchRequest(
                origin="YYZ",
                destination="JFK",
                departure_date=date(2024, 6, 15),
                max_stops=4
            )


class TestSegment:
    """Test Segment model."""

    def test_valid_segment(self, sample_segment):
        """Test creating a valid segment."""
        assert sample_segment.departure_airport == "YYZ"
        assert sample_segment.arrival_airport == "JFK"
        assert sample_segment.carrier == "AC"
        assert sample_segment.flight_number == "101"

    def test_segment_required_fields(self):
        """Test that all segment fields are required."""
        with pytest.raises(ValidationError):
            Segment(
                departure_airport="YYZ",
                arrival_airport="JFK"
                # Missing other required fields
            )


class TestItinerary:
    """Test Itinerary model."""

    def test_valid_itinerary(self, sample_itinerary):
        """Test creating a valid itinerary."""
        assert len(sample_itinerary.segments) == 1
        assert sample_itinerary.stops == 0
        assert sample_itinerary.total_duration == "3h"

    def test_itinerary_multiple_segments(self, sample_segment):
        """Test itinerary with multiple segments."""
        itinerary = Itinerary(
            segments=[sample_segment, sample_segment],
            total_duration="12h",
            stops=1
        )
        assert len(itinerary.segments) == 2
        assert itinerary.stops == 1


class TestFlightOffer:
    """Test FlightOffer model."""

    def test_valid_offer(self, sample_flight_offer):
        """Test creating a valid flight offer."""
        assert sample_flight_offer.id == "1"
        assert sample_flight_offer.price == 500.00
        assert sample_flight_offer.currency == "USD"
        assert sample_flight_offer.cabin_class == "economy"
        assert sample_flight_offer.is_refundable == True

    def test_offer_booking_url_optional(self, sample_itinerary):
        """Test creating offer without booking URL."""
        offer = FlightOffer(
            id="2",
            price=600.00,
            currency="USD",
            itineraries=[sample_itinerary],
            cabin_class="business",
            seats_available=None,
            is_refundable=None
        )
        assert offer.booking_url is None
        assert offer.booking_agent is None

    def test_offer_seats_optional(self, sample_itinerary):
        """Test that seats_available is optional."""
        offer = FlightOffer(
            id="3",
            price=700.00,
            currency="USD",
            itineraries=[sample_itinerary],
            cabin_class="first",
            seats_available=None,
            is_refundable=False
        )
        assert offer.seats_available is None


class TestPriceInsights:
    """Test PriceInsights model."""

    def test_valid_price_insights(self, sample_price_insights):
        """Test creating valid price insights."""
        assert sample_price_insights.lowest_price == 450.00
        assert sample_price_insights.price_level == "typical"
        assert sample_price_insights.typical_price_low == 400.00
        assert sample_price_insights.typical_price_high == 600.00

    def test_empty_price_insights(self):
        """Test that all price insights fields are optional."""
        insights = PriceInsights()
        assert insights.lowest_price is None
        assert insights.price_level is None
        assert insights.typical_price_low is None
        assert insights.typical_price_high is None


class TestFlightSearchResponse:
    """Test FlightSearchResponse model."""

    def test_valid_response(self, sample_flight_offer, sample_price_insights):
        """Test creating a valid search response."""
        response = FlightSearchResponse(
            origin="YYZ",
            destination="JFK",
            departure_date="2024-06-15",
            results_count=1,
            currency="USD",
            offers=[sample_flight_offer],
            price_insights=sample_price_insights
        )
        assert response.origin == "YYZ"
        assert response.destination == "JFK"
        assert response.results_count == 1
        assert len(response.offers) == 1

    def test_response_without_price_insights(self, sample_flight_offer):
        """Test creating response without price insights."""
        response = FlightSearchResponse(
            origin="LAX",
            destination="FRA",
            departure_date="2024-07-01",
            results_count=5,
            currency="EUR",
            offers=[sample_flight_offer]
        )
        assert response.price_insights is None

    def test_response_empty_offers(self):
        """Test creating response with no offers."""
        response = FlightSearchResponse(
            origin="SFO",
            destination="CDG",
            departure_date="2024-08-01",
            results_count=0,
            currency="USD",
            offers=[]
        )
        assert response.results_count == 0
        assert len(response.offers) == 0
