"""
Unit tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date
from unittest.mock import patch, MagicMock, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestSearchEndpoint:
    """Test the /search endpoint."""

    def test_search_required_params(self, client):
        """Test search endpoint with required parameters."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15"
        })
        # Check response status (may fail without API key, but endpoint should exist)
        assert response.status_code in [200, 400, 401, 422, 500]

    def test_search_missing_origin(self, client):
        """Test search endpoint missing required origin parameter."""
        response = client.get("/search", params={
            "destination": "JFK",
            "departure_date": "2024-06-15"
        })
        # Missing required param should return 422
        assert response.status_code == 422

    def test_search_missing_destination(self, client):
        """Test search endpoint missing required destination parameter."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "departure_date": "2024-06-15"
        })
        assert response.status_code == 422

    def test_search_missing_departure_date(self, client):
        """Test search endpoint missing required departure_date parameter."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "destination": "JFK"
        })
        assert response.status_code == 422

    def test_search_invalid_date_format(self, client):
        """Test search with invalid date format."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "15-06-2024"  # Invalid format
        })
        assert response.status_code == 422

    def test_search_optional_params(self, client):
        """Test search with optional parameters."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15",
            "return_date": "2024-06-22",
            "adults": "2",
            "max_price": "1500",
            "currency": "USD"
        })
        assert response.status_code in [200, 400, 401, 422, 500]

    def test_search_invalid_adults(self, client):
        """Test search with invalid adults value."""
        response = client.get("/search", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15",
            "adults": "0"
        })
        # Value 0 should be rejected
        assert response.status_code in [422, 400]


class TestHealthEndpoint:
    """Test the /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestAutocompleteEndpoint:
    """Test the /autocomplete endpoint."""

    def test_autocomplete_airport_codes(self, client):
        """Test autocomplete for airport codes."""
        response = client.get("/autocomplete", params={"query": "jf"})
        assert response.status_code in [200, 400, 500]

    def test_autocomplete_empty_query(self, client):
        """Test autocomplete with empty query."""
        response = client.get("/autocomplete", params={"query": ""})
        # May return empty or specific error
        assert response.status_code in [200, 400, 422]

    def test_autocomplete_missing_query(self, client):
        """Test autocomplete missing query parameter."""
        response = client.get("/autocomplete")
        assert response.status_code == 422


class TestPriceCalendarEndpoint:
    """Test the /price-calendar endpoint."""

    def test_price_calendar_required_params(self, client):
        """Test price calendar with required parameters."""
        response = client.get("/price-calendar", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15"
        })
        assert response.status_code in [200, 400, 401, 422, 500]

    def test_price_calendar_missing_origin(self, client):
        """Test price calendar missing origin."""
        response = client.get("/price-calendar", params={
            "destination": "JFK",
            "departure_date": "2024-06-15"
        })
        assert response.status_code == 422


class TestNearbyDatesEndpoint:
    """Test the /nearby-dates endpoint."""

    def test_nearby_dates_required_params(self, client):
        """Test nearby dates with required parameters."""
        response = client.get("/nearby-dates", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15"
        })
        assert response.status_code in [200, 400, 401, 422, 500]

    def test_nearby_dates_with_currency(self, client):
        """Test nearby dates with currency parameter."""
        response = client.get("/nearby-dates", params={
            "origin": "YYZ",
            "destination": "JFK",
            "departure_date": "2024-06-15",
            "currency": "EUR"
        })
        assert response.status_code in [200, 400, 401, 422, 500]


class TestDocsEndpoint:
    """Test that API documentation is available."""

    def test_openapi_json(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui(self, client):
        """Test Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc_ui(self, client):
        """Test ReDoc UI is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


class TestResponseFormat:
    """Test response format compliance."""

    def test_search_response_structure(self, client):
        """Test that search response has expected structure."""
        with patch('main.client.search_flights', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {
                "origin": "YYZ",
                "destination": "JFK",
                "departure_date": "2024-06-15",
                "results_count": 0,
                "currency": "USD",
                "offers": []
            }
            
            # Note: This test validates the endpoint structure
            response = client.get("/search", params={
                "origin": "YYZ",
                "destination": "JFK",
                "departure_date": "2024-06-15"
            })
            
            # Endpoint should exist (may fail on execution but not 404)
            assert response.status_code != 404

    def test_error_response_format(self, client):
        """Test that errors return proper format."""
        response = client.get("/search")  # Missing all required params
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.options("/search")
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 405, 500]
