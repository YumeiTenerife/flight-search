"""
Email sender using Resend API.
Sign up free at https://resend.com — 3,000 emails/month free.
Set RESEND_API_KEY in your .env file.
"""

import os
import httpx

RESEND_URL = "https://api.resend.com/emails"


class EmailError(Exception):
    pass


async def send_alert_email(
    to_email: str,
    origin: str,
    destination: str,
    offers: list,
    currency: str,
    alert_id: str,
):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise EmailError("RESEND_API_KEY not set in .env")

    from_email = os.getenv("RESEND_FROM_EMAIL", "alerts@yourdomain.com")

    CURRENCY_SYMBOLS = {"USD": "$", "CAD": "CA$", "EUR": "€", "GBP": "£", "AUD": "A$"}
    sym = CURRENCY_SYMBOLS.get(currency, currency + " ")

    # Build offer rows for the email
    offer_rows = ""
    for o in offers[:5]:  # show top 5
        price = f"{sym}{o['price']:,.0f}"
        cabin = o.get("cabin_class", "").replace("_", " ").title()
        itin = o.get("itineraries", [{}])[0]
        segs = itin.get("segments", [{}])
        dep_time = segs[0].get("departure_time", "")[:16].replace("T", " ") if segs else ""
        stops = itin.get("stops", 0)
        stops_label = "Non-stop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
        booking_url = o.get("booking_url", "")
        book_link = f'<a href="{booking_url}" style="color:#c9a84c;">Book →</a>' if booking_url else ""

        offer_rows += f"""
        <tr style="border-bottom:1px solid #1e1e2a;">
          <td style="padding:10px 8px;color:#f0ede6;font-size:14px;">{dep_time}</td>
          <td style="padding:10px 8px;color:#f0ede6;font-size:14px;">{stops_label}</td>
          <td style="padding:10px 8px;color:#f0ede6;font-size:14px;">{cabin}</td>
          <td style="padding:10px 8px;color:#e8c97a;font-size:16px;font-weight:700;">{price}</td>
          <td style="padding:10px 8px;font-size:14px;">{book_link}</td>
        </tr>
        """

    unsubscribe_url = f"http://localhost:8000/alerts/{alert_id}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="background:#0a0a0f;margin:0;padding:24px;font-family:'DM Sans',Arial,sans-serif;">
      <div style="max-width:600px;margin:0 auto;">

        <div style="margin-bottom:24px;">
          <span style="font-size:20px;color:#c9a84c;">✈</span>
          <span style="font-size:20px;font-weight:700;color:#f0ede6;margin-left:8px;">Skyline</span>
        </div>

        <div style="background:#16161f;border:1px solid #1e1e2a;border-radius:12px;padding:24px;margin-bottom:16px;">
          <h2 style="color:#f0ede6;margin:0 0 6px;">New flights found</h2>
          <p style="color:#9996a0;margin:0 0 20px;font-size:14px;">
            {origin} → {destination} · {len(offers)} flight{'s' if len(offers) != 1 else ''} matching your alert
          </p>

          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="border-bottom:1px solid #2a2a3a;">
                <th style="padding:8px;color:#5a5868;font-size:11px;text-align:left;text-transform:uppercase;letter-spacing:.08em;">Departure</th>
                <th style="padding:8px;color:#5a5868;font-size:11px;text-align:left;text-transform:uppercase;letter-spacing:.08em;">Stops</th>
                <th style="padding:8px;color:#5a5868;font-size:11px;text-align:left;text-transform:uppercase;letter-spacing:.08em;">Class</th>
                <th style="padding:8px;color:#5a5868;font-size:11px;text-align:left;text-transform:uppercase;letter-spacing:.08em;">Price</th>
                <th style="padding:8px;color:#5a5868;font-size:11px;text-align:left;text-transform:uppercase;letter-spacing:.08em;"></th>
              </tr>
            </thead>
            <tbody>{offer_rows}</tbody>
          </table>
        </div>

        <p style="color:#5a5868;font-size:12px;text-align:center;">
          You're receiving this because you set a flight alert on Skyline.<br>
          <a href="{unsubscribe_url}" style="color:#5a5868;">Manage or cancel this alert</a>
        </p>
      </div>
    </body>
    </html>
    """

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [to_email],
                "subject": f"✈ New flights: {origin} → {destination}",
                "html": html,
            },
            timeout=10.0,
        )

    if resp.status_code not in (200, 201):
        raise EmailError(f"Resend API error {resp.status_code}: {resp.text}")
