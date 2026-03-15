#!/usr/bin/env python3
"""
Flight Search CLI
Usage: python cli.py search --from YYZ --to LHR --date 2026-06-15
"""

import asyncio
import click
from datetime import date, datetime
from typing import Optional

from amadeus_client import AmadeusClient, AmadeusAuthError, AmadeusSearchError
from models import FlightOffer


# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_price(price: float, currency: str) -> str:
    symbols = {"USD": "$", "EUR": "€", "CAD": "CA$", "GBP": "£"}
    sym = symbols.get(currency, f"{currency} ")
    return f"{sym}{price:,.2f}"


def fmt_time(iso_dt: str) -> str:
    """Parse ISO 8601 datetime and return HH:MM."""
    try:
        return datetime.fromisoformat(iso_dt).strftime("%H:%M")
    except ValueError:
        return iso_dt


def fmt_date(iso_dt: str) -> str:
    try:
        return datetime.fromisoformat(iso_dt).strftime("%d %b")
    except ValueError:
        return ""


def print_offer(idx: int, offer: FlightOffer, currency: str):
    price_str = fmt_price(offer.price, currency)
    click.echo(f"\n  {'─'*60}")
    click.echo(f"  #{idx}  {click.style(price_str, fg='green', bold=True)}  "
               f"│  {offer.cabin_class.title()}  "
               f"│  {offer.seats_available or '?'} seats left")

    for leg_idx, itin in enumerate(offer.itineraries):
        label = "Outbound" if leg_idx == 0 else "Return  "
        stops_label = (
            click.style("Non-stop", fg="cyan")
            if itin.stops == 0
            else click.style(f"{itin.stops} stop{'s' if itin.stops > 1 else ''}", fg="yellow")
        )
        click.echo(f"\n     {label}  ·  {itin.total_duration}  ·  {stops_label}")

        for seg in itin.segments:
            dep_time = fmt_time(seg.departure_time)
            arr_time = fmt_time(seg.arrival_time)
            dep_date = fmt_date(seg.departure_time)
            arr_date = fmt_date(seg.arrival_time)
            click.echo(
                f"       {dep_time} {seg.departure_airport}  ──({seg.duration})──▶  "
                f"{arr_time} {seg.arrival_airport}   "
                f"{click.style(seg.flight_number, dim=True)}  {dep_date}"
            )


# ── CLI commands ──────────────────────────────────────────────────────────────

@click.group()
def cli():
    """✈  Flight Search CLI — powered by Amadeus"""
    pass


@cli.command()
@click.option("--from", "origin", required=True, help="Origin IATA code (e.g. YYZ)")
@click.option("--to", "destination", required=True, help="Destination IATA code (e.g. LHR)")
@click.option("--date", "departure_date", required=True,
              type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Departure date YYYY-MM-DD")
@click.option("--return-date", "return_date", default=None,
              type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Return date for round-trips (YYYY-MM-DD)")
@click.option("--adults", default=1, show_default=True, help="Number of adult passengers")
@click.option("--max-price", default=None, type=float, help="Max total price")
@click.option("--max-stops", default=None, type=int, help="Max stops (0 = non-stop)")
@click.option("--currency", default="USD", show_default=True, help="Currency (USD, EUR, CAD…)")
@click.option("--sort", "sort_by",
              type=click.Choice(["price", "stops", "duration"], case_sensitive=False),
              default="price", show_default=True, help="Sort results by")
@click.option("--limit", default=10, show_default=True, help="Max results to display")
def search(origin, destination, departure_date, return_date, adults,
           max_price, max_stops, currency, sort_by, limit):
    """Search for available flights."""

    dep_date: date = departure_date.date()
    ret_date: Optional[date] = return_date.date() if return_date else None

    if ret_date and ret_date <= dep_date:
        click.echo(click.style("Error: return-date must be after departure date.", fg="red"))
        raise SystemExit(1)

    trip_type = "Round-trip" if ret_date else "One-way"
    click.echo(
        f"\n  ✈  Searching {trip_type}  "
        f"{click.style(origin.upper(), bold=True)} → "
        f"{click.style(destination.upper(), bold=True)}  "
        f"· {dep_date}"
        + (f" → {ret_date}" if ret_date else "")
        + f"  · {adults} adult(s)"
    )
    if max_price:
        click.echo(f"     Filter: max price {fmt_price(max_price, currency)}")
    if max_stops is not None:
        click.echo(f"     Filter: max {max_stops} stop(s)")
    click.echo()

    try:
        client = AmadeusClient()
    except AmadeusAuthError as e:
        click.echo(click.style(f"\n  ✗  {e}", fg="red"))
        raise SystemExit(1)

    async def run():
        offers = await client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=dep_date,
            return_date=ret_date,
            adults=adults,
            currency=currency,
        )

        # Filter
        if max_price is not None:
            offers = [o for o in offers if o.price <= max_price]
        if max_stops is not None:
            offers = [o for o in offers if all(i.stops <= max_stops for i in o.itineraries)]

        # Sort
        if sort_by == "price":
            offers.sort(key=lambda o: o.price)
        elif sort_by == "stops":
            offers.sort(key=lambda o: o.itineraries[0].stops if o.itineraries else 99)
        elif sort_by == "duration":
            offers.sort(key=lambda o: o.itineraries[0].total_duration if o.itineraries else "")

        return offers

    try:
        with click.progressbar(length=1, label="  Fetching results") as bar:
            offers = asyncio.run(run())
            bar.update(1)
    except AmadeusSearchError as e:
        click.echo(click.style(f"\n  ✗  Search error: {e}", fg="red"))
        raise SystemExit(1)
    except Exception as e:
        click.echo(click.style(f"\n  ✗  Unexpected error: {e}", fg="red"))
        raise SystemExit(1)

    if not offers:
        click.echo(click.style("\n  No flights found matching your criteria.", fg="yellow"))
        return

    display = offers[:limit]
    click.echo(
        f"\n  Found {click.style(str(len(offers)), bold=True)} offer(s)"
        f" — showing top {len(display)} sorted by {sort_by}\n"
    )

    for idx, offer in enumerate(display, 1):
        print_offer(idx, offer, currency)

    click.echo(f"\n  {'─'*60}\n")


@cli.command()
@click.argument("iata_code")
def airport(iata_code):
    """Look up an airport by IATA code (basic reference)."""
    common = {
        "YYZ": "Toronto Pearson International, Canada",
        "YVR": "Vancouver International, Canada",
        "YUL": "Montréal–Trudeau International, Canada",
        "JFK": "John F. Kennedy International, New York, USA",
        "LAX": "Los Angeles International, USA",
        "ORD": "O'Hare International, Chicago, USA",
        "LHR": "Heathrow, London, UK",
        "CDG": "Charles de Gaulle, Paris, France",
        "AMS": "Amsterdam Schiphol, Netherlands",
        "DXB": "Dubai International, UAE",
        "SIN": "Singapore Changi, Singapore",
        "NRT": "Narita International, Tokyo, Japan",
        "SYD": "Sydney Kingsford Smith, Australia",
    }
    code = iata_code.upper()
    name = common.get(code)
    if name:
        click.echo(f"\n  {click.style(code, bold=True)} — {name}\n")
    else:
        click.echo(f"\n  {code} — unknown code (check https://www.iata.org/en/publications/directories/code-search/)\n")


if __name__ == "__main__":
    cli()
