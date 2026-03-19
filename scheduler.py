"""
Background scheduler — runs once a day and checks all saved alerts.
Uses APScheduler with AsyncIOScheduler so it integrates cleanly with FastAPI.
"""

import json
import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import get_all_alerts, update_alert_run
from email_sender import send_alert_email

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_alerts():
    """Run all saved alerts and send emails where new flights are found."""
    from amadeus_client import AmadeusClient, AmadeusAuthError

    try:
        client = AmadeusClient()
    except AmadeusAuthError:
        logger.error("Scheduler: SerpApi key not configured, skipping alert run.")
        return

    alerts = get_all_alerts()
    logger.info(f"Scheduler: checking {len(alerts)} alert(s)...")

    for alert in alerts:
        try:
            await process_alert(client, alert)
        except Exception as e:
            logger.error(f"Scheduler: error processing alert {alert['id']}: {e}")


async def process_alert(client, alert: dict):
    filters = json.loads(alert["filters"])
    last_offers_raw = alert.get("last_offers")
    last_seen_ids = set()
    if last_offers_raw:
        try:
            last_seen_ids = {o["id"] for o in json.loads(last_offers_raw)}
        except Exception:
            pass

    dep_date_str = filters.get("departure_date")
    if not dep_date_str:
        return

    try:
        dep_date = date.fromisoformat(dep_date_str)
    except ValueError:
        return

    # Skip alerts with past dates
    if dep_date < date.today():
        logger.info(f"Scheduler: alert {alert['id']} has past date {dep_date_str}, skipping.")
        return

    offers, _ = await client.search_flights(
        origin=alert["origin"],
        destination=alert["destination"],
        departure_date=dep_date,
        return_date=date.fromisoformat(filters["return_date"]) if filters.get("return_date") else None,
        adults=int(filters.get("adults", 1)),
        currency=filters.get("currency", "USD"),
        max_results=10,
    )

    if not offers:
        logger.info(f"Scheduler: no flights found for alert {alert['id']}")
        return

    # Apply the same filters saved with the alert
    from main import apply_filters
    offers = apply_filters(
        offers,
        max_price=filters.get("max_price"),
        max_stops=int(filters["max_stops"]) if filters.get("max_stops") else None,
        no_overnight_layover=filters.get("no_overnight_layover", False),
        avoid_countries=filters.get("avoid_countries"),
    )

    if not offers:
        return

    # Serialize offers for comparison and storage
    offers_data = [
        {
            "id": o.id,
            "price": o.price,
            "cabin_class": o.cabin_class,
            "booking_url": o.booking_url,
            "itineraries": [
                {
                    "stops": itin.stops,
                    "total_duration": itin.total_duration,
                    "segments": [
                        {
                            "departure_airport": s.departure_airport,
                            "arrival_airport": s.arrival_airport,
                            "departure_time": s.departure_time,
                            "arrival_time": s.arrival_time,
                            "carrier": s.carrier,
                            "flight_number": s.flight_number,
                        }
                        for s in itin.segments
                    ],
                }
                for itin in o.itineraries
            ],
        }
        for o in offers
    ]

    # Find new offers not seen in last run
    new_offers = [o for o in offers_data if o["id"] not in last_seen_ids]

    # Always send on first run (no last_offers yet), or when new flights appear
    if not last_offers_raw or new_offers:
        logger.info(
            f"Scheduler: sending alert email to {alert['email']} — "
            f"{len(new_offers)} new offer(s) for {alert['origin']}→{alert['destination']}"
        )
        await send_alert_email(
            to_email=alert["email"],
            origin=alert["origin"],
            destination=alert["destination"],
            offers=offers_data,
            currency=filters.get("currency", "USD"),
            alert_id=alert["id"],
        )
    else:
        logger.info(f"Scheduler: no new flights for alert {alert['id']}, skipping email.")

    update_alert_run(alert["id"], offers_data)


def start_scheduler():
    scheduler.add_job(
        check_all_alerts,
        trigger=IntervalTrigger(hours=24),
        id="check_alerts",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler started — alerts will be checked every 24 hours.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
