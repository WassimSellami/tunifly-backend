import os
import platform
import logging
from datetime import datetime
import requests
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.crud import subscription as crud_subscription
from app.services import booking_url_service

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

logger = logging.getLogger("flight_alerts")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def _send_email(to_email: str, subject: str, plain_text: str, html: str) -> bool:
    if not RESEND_API_KEY or not EMAIL_FROM:
        logger.error(
            "Email was not sent because RESEND_API_KEY or EMAIL_FROM is not configured."
        )
        return False

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "User-Agent": "tunifly-backend/1.0",
            },
            json={
                "from": EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "text": plain_text,
                "html": html,
            },
            timeout=15,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_welcome_email(to_email: str) -> None:
    subject = "Welcome to TuniFly"
    plain_text = (
        "Welcome to TuniFly!\n\n"
        "You can now track flights and create price alerts. "
        "We will email you when a watched flight reaches your target price.\n\n"
        "Happy travels!"
    )
    html = """
    <html><body>
        <h2>Welcome to TuniFly!</h2>
        <p>You can now track flights and create price alerts.</p>
        <p>We will email you when a watched flight reaches your target price.</p>
        <p>Happy travels!</p>
    </body></html>
    """
    if _send_email(to_email, subject, plain_text, html):
        logger.info(f"Welcome email sent to {to_email}")


def send_price_alert_email(
    to_email: str, flight_details: dict, target_price: float, current_price: float
):
    raw_date = flight_details.get("departureDate")
    day_format_specifier = "%#d" if platform.system() == "Windows" else "%-d"

    try:
        if isinstance(raw_date, datetime):
            date_format = f"{day_format_specifier} %b %Y"
            departure_date = raw_date.strftime(date_format)
        else:
            date_format = f"{day_format_specifier} %b %Y"
            departure_date = datetime.fromisoformat(str(raw_date)).strftime(date_format)
    except Exception as e:
        logger.warning(f"Failed to parse departure date: {e}")
        departure_date = str(raw_date)

    booking_url = flight_details.get("bookingUrl")

    subject = "✈️ Flight Price Alert"

    link_html = ""
    if booking_url:
        link_html = f"<p><a href='{booking_url}' style='display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;'>Book Now! ✈️</a></p>"

    html_body = f"""
    <html>
    <head></head>
    <body>
        <p>Good news! 🎉</p>
        <p>The flight you were watching has dropped below your target price.</p>
        <p>
            <strong>🛫 Flight:</strong> {flight_details.get('originAirportCode')} ➡️ {flight_details.get('arrivalAirportCode')}<br>
            <strong>📅 Departure Date:</strong> {departure_date}<br>
            <strong>🎯 Your Target Price:</strong> {target_price:.2f}€<br>
            <strong>💰 Current Price:</strong> {current_price:.2f}€
        </p>
        {link_html}
        <p><i>We will continue to notify you when this flight crosses your target price.</i></p>
        <p>Happy travels! 🧳</p>
    </body>
    </html>
    """

    plain_text_book_now_link = ""
    if booking_url:
        plain_text_book_now_link = f"Book Now: {booking_url}\n"

    plain_text_body = (
        f"Good news! 🎉\n\n"
        f"The flight you were watching has dropped below your target price.\n\n"
        f"🛫 Flight: {flight_details.get('originAirportCode')} ➡ {flight_details.get('arrivalAirportCode')}\n"
        f"📅 Departure Date: {departure_date}\n"
        f"🎯 Your Target Price: {target_price:.2f}€\n"
        f"💰 Current Price: {current_price:.2f}€\n"
        f"{plain_text_book_now_link}"
        f"📩 We will continue to notify you when this flight crosses your target price.\n\n"
        f"Happy travels! 🧳\n"
    )

    if _send_email(to_email, subject, plain_text_body, html_body):
        logger.info(f"Email sent to {to_email}")


def check_and_send_alerts_for_flights(db: Session, updated_flights_info: list):
    if not updated_flights_info:
        return
    logger.info("Checking subscriptions for recently updated flights...")
    for item in updated_flights_info:
        db_flight = item["flight"]
        old_price_eur = item.get("old_price_eur")

        if old_price_eur is None:
            continue

        subscriptions = crud_subscription.get_active_subscriptions_for_flight_with_notifications_enabled(
            db, db_flight.id
        )

        booking_url = booking_url_service.generate_nouvelair_booking_url(db_flight)

        for sub in subscriptions:
            target_price = sub.targetPrice
            updated_price_eur = db_flight.priceEur

            if (old_price_eur > target_price) and (updated_price_eur <= target_price):
                logger.info(f"ALERT TRIGGERED for {sub.user.email} on Flight {db_flight.id}")
                send_price_alert_email(
                    to_email=sub.user.email,
                    flight_details={
                        "originAirportCode": db_flight.departureAirportCode,
                        "arrivalAirportCode": db_flight.arrivalAirportCode,
                        "departureDate": db_flight.departureDate.isoformat(),
                        "bookingUrl": booking_url,
                    },
                    target_price=target_price,
                    current_price=updated_price_eur,
                )

            else:
                logger.debug(
                    f"Subscription {sub.id} for {sub.user.email} (Target: {target_price:.2f}€, Prev: {old_price_eur:.2f}€, New: {updated_price_eur:.2f}€) - No alert needed."
                )
    logger.info("Finished checking subscriptions for updated flights.")
