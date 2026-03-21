"""
Shared pytest fixtures and configuration for the test suite.
"""

import pytest
import sys
import os
from datetime import date
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import FlightSearchRequest, FlightOffer, Itinerary, Segment, PriceInsights


@pytest.fixture
def sample_flight_search_request():
    """Create a sample flight search request."""
    return FlightSearchRequest(
        origin="YYZ",
        destination="JFK",
        departure_date=date(2024, 6, 15),
        return_date=date(2024, 6, 22),
        adults=2,
        max_price=1500.00,
        currency="USD"
    )


@pytest.fixture
def sample_segment():
    """Create a sample flight segment."""
    return Segment(
        departure_airport="YYZ",
        arrival_airport="JFK",
        departure_time="09:00",
        arrival_time="12:00",
        carrier="AC",
        flight_number="101",
        duration="3h"
    )


@pytest.fixture
def sample_itinerary(sample_segment):
    """Create a sample itinerary."""
    return Itinerary(
        segments=[sample_segment],
        total_duration="3h",
        stops=0
    )


@pytest.fixture
def sample_flight_offer(sample_itinerary):
    """Create a sample flight offer."""
    return FlightOffer(
        id="1",
        price=500.00,
        currency="USD",
        itineraries=[sample_itinerary],
        seats_available=5,
        cabin_class="economy",
        is_refundable=True,
        booking_url="https://example.com/book",
        booking_agent="google_flights"
    )


@pytest.fixture
def sample_price_insights():
    """Create a sample price insights object."""
    return PriceInsights(
        lowest_price=450.00,
        price_level="typical",
        typical_price_low=400.00,
        typical_price_high=600.00
    )


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("SERPAPI_KEY", "test_key_12345")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
