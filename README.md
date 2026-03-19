# ✈ Flight Search — Advanced Flight Filtering Tool

A powerful flight search application that goes beyond standard flight search engines by providing **smart filtering options** that most websites don't offer. Built with **FastAPI backend** and **React frontend**, powered by [SerpApi's Google Flights API](https://serpapi.com/google-flights-api).

## 🎯 Why This Project Exists

Most flight search websites have frustrating limitations:
- **Country-based connection filtering**: Most sites only let you exclude specific airports, not entire countries
- **Overnight layover avoidance**: No easy way to avoid layovers longer than 6 hours between 11 PM and 6 AM
- **Group luggage pricing**: Websites calculate luggage per person, but you often want total cost for your group (e.g., 2 adults + 2 kids sharing 3 carry-ons)

This tool solves these problems with advanced filtering that actually works.

## ✨ Unique Features

### 🗺️ Country-Based Connection Filtering
- Avoid entire countries for layovers (not just individual airports)
- Perfect for travelers who want to avoid specific regions for security, visa, or comfort reasons

### 🌙 Overnight Layover Prevention
- Automatically exclude flights with layovers longer than 6 hours between 11 PM and 6 AM
- No more sleeping in airports or dealing with overnight security procedures

### 🧳 Smart Group Luggage Pricing
- Calculate total luggage costs for your entire group, not per person
- Example: 2 adults + 2 kids = 3 carry-ons total (not 4 separate calculations)

### 📊 Price Insights & Trends
- View price trends for ±3 days around your travel dates
- Make informed decisions about when to book

---

## 📁 Project Structure

```
flight_search/
├── backend/            # FastAPI REST API with advanced filtering
│   ├── main.py
│   ├── models.py
│   ├── amadeus_client.py
│   ├── requirements.txt
│   └── .env
└── frontend/           # React web interface
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   └── ...
    └── package.json
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

## 🚀 Running the Application

### Backend API
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### Frontend Web Interface
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

Visit **http://localhost:5173** to use the web interface with all filtering options.

---

## ⚠️ Round-Trip Note

Google Flights requires two API calls for round-trips (one for outbound, one for return legs). This means a round-trip search costs **2 of your 250 monthly credits**. One-way searches cost 1.

### GET /search

```
GET /search?origin=YYZ&destination=LHR&departure_date=2026-06-15&adults=1&currency=CAD&avoid_countries=RU,CN&no_overnight_layover=true&carry_on_bags=2&checked_bags=1
```

| Parameter              | Required | Description                            | Example        |
|-----------------------|----------|----------------------------------------|----------------|
| `origin`              | ✅       | Origin IATA code                       | `YYZ`          |
| `destination`         | ✅       | Destination IATA code                  | `LHR`          |
| `departure_date`      | ✅       | Date (YYYY-MM-DD)                      | `2026-06-15`   |
| `return_date`         | ❌       | Return date for round-trips            | `2026-06-25`   |
| `adults`              | ❌       | Adult passengers (default: 1)          | `2`            |
| `children`            | ❌       | Child passengers (default: 0)          | `2`            |
| `max_price`           | ❌       | Filter: max total price                | `800`          |
| `max_stops`           | ❌       | Filter: 0 = non-stop only              | `1`            |
| `currency`            | ❌       | Currency code (default: USD)           | `CAD`          |
| `sort_by`             | ❌       | `price` \| `stops` \| `duration`      | `price`        |
| `avoid_countries`     | ❌       | Comma-separated country codes to avoid | `RU,CN`        |
| `no_overnight_layover`| ❌       | Exclude layovers >6h between 23:00-06:00| `true`         |
| `carry_on_bags`       | ❌       | Total carry-on bags for group          | `3`            |
| `checked_bags`        | ❌       | Total checked bags for group           | `2`            |

### POST /search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "YYZ",
    "destination": "CDG",
    "departure_date": "2026-06-15",
    "adults": 2,
    "children": 2,
    "max_price": 1200,
    "max_stops": 1,
    "currency": "USD",
    "avoid_countries": "RU,CN",
    "no_overnight_layover": true,
    "carry_on_bags": 3,
    "checked_bags": 1
  }'
```

---

## ⚠️ Round-Trip Note

Google Flights requires two API calls for round-trips (one for outbound, one for return legs). This means a round-trip search costs **2 of your 250 monthly credits**. One-way searches cost 1.

---

## 🛠 Extending the App

The project already includes:
- ✅ **React frontend** — Full web interface with all filtering options
- ✅ **Airport autocomplete** — SerpApi integration for airport suggestions
- ✅ **Price trends** — ±3 day price analysis around your dates
- ✅ **Advanced filtering** — Country avoidance, overnight layover prevention, group luggage pricing

### Future Enhancements
- **Price alerts** — Get notified when prices drop
- **Deep search** — Add `deep_search=true` for results identical to the browser (slower)
- **Mobile app** — React Native version for iOS/Android
- **Multi-city searches** — Complex itineraries with multiple destinations

---

## 🤖 Built with AI

This project was **created with AI assistance** from:
- **Claude** (Anthropic) — Backend architecture, API design, database setup, deployment configuration, and advanced flight filtering logic
- **GitHub Copilot** — Frontend React components, styling, and UI interactions

