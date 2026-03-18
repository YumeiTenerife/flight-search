# ✈ Flight Search — Python + SerpApi (Google Flights)

A Skyscanner-style flight search tool with a **FastAPI REST backend** and a **CLI interface**, powered by [SerpApi's Google Flights API](https://serpapi.com/google-flights-api).

---

## 📁 Project Structure

```
flight_search/
├── main.py             # FastAPI REST API
├── cli.py              # Command-line interface
├── amadeus_client.py   # SerpApi client (drop-in, same interface)
├── models.py           # Pydantic data models
├── requirements.txt
└── .env                # Your API key (create this)
```

---

## 🔑 1. Get a Free SerpApi Key

1. Sign up at [https://serpapi.com/users/sign_up](https://serpapi.com/users/sign_up) — instant, no approval
2. Copy your **API Key** from the dashboard
3. Free plan: **250 searches/month** — no credit card required

---

## ⚙️ 2. Configure Credentials

Create a `.env` file:

```env
SERPAPI_KEY=your_api_key_here
```

Or export directly:

```bash
export SERPAPI_KEY=your_api_key_here
```

---

## 📦 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 REST API Usage

```bash
uvicorn main:app --reload
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### GET /search

```
GET /search?origin=YYZ&destination=LHR&departure_date=2026-06-15&adults=1&currency=CAD
```

| Parameter         | Required | Description                            | Example        |
|------------------|----------|----------------------------------------|----------------|
| `origin`         | ✅       | Origin IATA code                       | `YYZ`          |
| `destination`    | ✅       | Destination IATA code                  | `LHR`          |
| `departure_date` | ✅       | Date (YYYY-MM-DD)                      | `2026-06-15`   |
| `return_date`    | ❌       | Return date for round-trips            | `2026-06-25`   |
| `adults`         | ❌       | Passengers (default: 1)                | `2`            |
| `max_price`      | ❌       | Filter: max total price                | `800`          |
| `max_stops`      | ❌       | Filter: 0 = non-stop only              | `1`            |
| `currency`       | ❌       | Currency code (default: USD)           | `CAD`          |
| `sort_by`        | ❌       | `price` \| `stops` \| `duration`      | `price`        |

### POST /search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "YYZ",
    "destination": "CDG",
    "departure_date": "2026-06-15",
    "adults": 2,
    "max_price": 1200,
    "max_stops": 1,
    "currency": "USD"
  }'
```

---

## 💻 CLI Usage

```bash
# One-way search
python cli.py search --from YYZ --to LHR --date 2026-06-15

# Round-trip with filters
python cli.py search --from YYZ --to CDG \
  --date 2026-06-15 --return-date 2026-06-25 \
  --adults 2 --max-price 1500 --max-stops 1 --currency CAD

# Non-stop only
python cli.py search --from YYZ --to JFK --date 2026-07-01 --max-stops 0

# Airport lookup
python cli.py airport LHR
```

---

## ⚠️ Round-Trip Note

Google Flights requires two API calls for round-trips (one for outbound, one for return legs). This means a round-trip search costs **2 of your 250 monthly credits**. One-way searches cost 1.

---

## 🛠 Extending the App

- **Airport autocomplete** — SerpApi has a `google_flights_autocomplete` engine
- **Price calendar** — find cheapest dates using the `google_travel_explore` engine
- **Deep search** — add `deep_search=true` for results identical to the browser (slower)
- **React frontend** — call your FastAPI backend from a web UI
