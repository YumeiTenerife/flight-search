# Backend Unit Tests

Comprehensive unit test suite for the Flight Search backend API.

## Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

This includes:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities

## Running Tests

### Run all tests:
```bash
pytest
```

### Run tests with verbose output:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest tests/test_models.py
```

### Run specific test class:
```bash
pytest tests/test_models.py::TestFlightSearchRequest
```

### Run specific test:
```bash
pytest tests/test_models.py::TestFlightSearchRequest::test_valid_request
```

### Run tests with coverage report:
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

## Test Structure

### `conftest.py`
Shared pytest fixtures used across all tests:
- `sample_flight_search_request` - Valid flight search request object
- `sample_segment` - Flight segment fixture
- `sample_itinerary` - Flight itinerary fixture
- `sample_flight_offer` - Complete flight offer fixture
- `sample_price_insights` - Price insights fixture
- `mock_env` - Mock environment variables

### `test_models.py`
Tests for Pydantic data models:
- ✅ `FlightSearchRequest` validation (required fields, constraints)
- ✅ `Segment` model validation
- ✅ `Itinerary` composition and validation
- ✅ `FlightOffer` with optional fields
- ✅ `PriceInsights` optional data
- ✅ `FlightSearchResponse` complete structure

Key tests:
- Valid model creation
- Field validation constraints (min/max values)
- Optional field handling
- Invalid input rejection

### `test_amadeus_client.py`
Tests for the SerpAPI Google Flights client:
- ✅ Client initialization with/without API key
- ✅ Parameters building for different cabin classes
- ✅ Baggage parameter handling
- ✅ Async search functionality (mocked)
- ✅ Error handling (auth, rate limit, network)
- ✅ Cabin class name mapping

Key tests:
- API key validation
- Request parameter construction
- HTTP error responses
- Search request formatting

### `test_main.py`
Tests for FastAPI endpoints:
- ✅ `/search` endpoint with required/optional parameters
- ✅ `/health` endpoint
- ✅ `/autocomplete` endpoint
- ✅ `/price-calendar` endpoint
- ✅ `/nearby-dates` endpoint
- ✅ API documentation endpoints (`/docs`, `/redoc`)
- ✅ OpenAPI schema availability
- ✅ CORS configuration
- ✅ Error response format

Key tests:
- Parameter validation
- Required vs optional fields
- Invalid date format handling
- HTTP status codes
- Response structure

### `test_database.py`
Tests for database operations:
- ✅ Database initialization and table creation
- ✅ Database connection handling
- ✅ Alert storage operations
- ✅ Alert retrieval operations
- ✅ Error handling and edge cases

Key tests:
- Connection management
- Table creation verification
- Data persistence operations
- Error scenarios

## Test Coverage

Current test coverage includes:

| Module | Coverage | Test Count |
|--------|----------|-----------|
| models.py | High | 45+ tests |
| amadeus_client.py | High | 25+ tests |
| main.py (endpoints) | Medium | 30+ tests |
| database.py | Medium | 20+ tests |
| **Total** | **70%+** | **120+ tests** |

## Key Testing Patterns

### 1. Fixtures
Reusable test data in `conftest.py`:
```python
def test_with_fixture(sample_flight_search_request):
    assert sample_flight_search_request.origin == "YYZ"
```

### 2. Mocking
Mock external API calls and database:
```python
with patch('amadeus_client._get', new_callable=AsyncMock) as mock_get:
    mock_get.return_value = {...}
    await client.search_flights(...)
```

### 3. Parametrization
Test multiple scenarios:
```python
@pytest.mark.parametrize("cabin,code", [
    ("economy", "1"),
    ("business", "3")
])
def test_cabin_codes(cabin, code):
    ...
```

### 4. Async Testing
Test async functions:
```python
@pytest.mark.asyncio
async def test_search_flights_success():
    result = await client.search_flights(...)
```

## Continuous Integration

The test suite can be integrated into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Adding New Tests

1. Create test file in `tests/` directory: `tests/test_new_feature.py`
2. Import fixtures from `conftest.py`
3. Follow naming convention: `test_*.py` files, `test_*` functions
4. Use descriptive names and docstrings
5. Organize into test classes by functionality

Example:
```python
class TestNewFeature:
    """Test description."""
    
    def test_success_case(self, mock_env):
        """Test description."""
        assert True
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            ...
```

## Environment Variables for Tests

Tests use mock environment variables via the `mock_env` fixture:
- `SERPAPI_KEY=test_key_12345`
- `DATABASE_URL=sqlite:///:memory:`

Override in specific tests:
```python
def test_specific(monkeypatch):
    monkeypatch.setenv("CUSTOM_VAR", "value")
```

## Troubleshooting

### "No module named 'main'"
Make sure you're running pytest from the `backend/` directory.

### Async test failures
Install `pytest-asyncio`: `pip install pytest-asyncio`

### Import errors
Ensure `sys.path` includes parent directory in test files.

### Coverage not working
Install: `pip install pytest-cov`

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
