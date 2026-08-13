import os
import platform
import logging
from datetime import datetime
from html import escape
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
    subject = "Welcome to TuniFly - Your Flight Tracker Is Ready"
    plain_text = (
        "Welcome to TuniFly!\n\n"
        "You can now track flights and create price alerts.\n"
        "We'll email you when a watched flight reaches your target price.\n\n"
        "Happy travels!\n"
        "- The TuniFly Team"
    )
    html = """
    <!doctype html>
    <html lang="en">
    <body style="margin:0; padding:0; background-color:#f4f8fc; font-family:Arial, Helvetica, sans-serif; color:#16324f;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f8fc;">
            <tr><td align="center" style="padding:32px 16px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; background-color:#ffffff; border-radius:16px; overflow:hidden;">
                    <tr><td align="center" style="background-color:#e70013; padding:36px 24px; color:#ffffff;">
                        <div style="font-size:28px; font-weight:700; letter-spacing:-1px;">Tuni<span style="color:#ffffff;">Fly</span> &#9992;</div>
                        <div style="margin-top:12px; font-size:16px; line-height:24px;">Your smart flight tracker is ready to go</div>
                    </td></tr>
                    <tr><td style="padding:36px 30px; font-size:16px; line-height:25px;">
                        <p style="margin:0 0 20px; font-size:18px;"><strong>Welcome aboard!</strong> You can now track flights and create price alerts.</p>
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:20px 0; background-color:#fdf1f2; border-left:4px solid #e70013; border-radius:8px;">
                            <tr><td style="padding:18px 20px;"><strong style="color:#c40010;">Track your flights</strong><br><span style="color:#52677d;">Monitor flight prices and never miss a deal.</span></td></tr>
                        </table>
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:20px 0; background-color:#fdf1f2; border-left:4px solid #e70013; border-radius:8px;">
                            <tr><td style="padding:18px 20px;"><strong style="color:#c40010;">Smart price alerts</strong><br><span style="color:#52677d;">We'll email you when a watched flight reaches your target price.</span></td></tr>
                        </table>
                        <p style="margin:28px 0 0; color:#52677d;">Happy travels!<br><em>- The TuniFly Team</em></p>
                    </td></tr>
                    <tr><td align="center" style="padding:24px; background-color:#102a43; color:#d9e4ee; font-size:13px; line-height:20px;">
                        <span style="color:#9db3c8;">&copy; 2026 TuniFly. All rights reserved.</span>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
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
        link_html = f"""
        <tr><td align="center" style="padding:8px 30px 30px;">
            <a href="{escape(str(booking_url), quote=True)}" style="display:inline-block; padding:13px 26px; background-color:#e70013; color:#ffffff; text-decoration:none; border-radius:6px; font-weight:700;">View flight</a>
        </td></tr>
        """

    origin = escape(str(flight_details.get("originAirportCode", "")))
    destination = escape(str(flight_details.get("arrivalAirportCode", "")))

    html_body = f"""
    <!doctype html>
    <html lang="en">
    <body style="margin:0; padding:0; background-color:#f4f8fc; font-family:Arial, Helvetica, sans-serif; color:#16324f;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f8fc;"><tr><td align="center" style="padding:32px 16px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:600px; background-color:#ffffff; border-radius:16px; overflow:hidden;">
                <tr><td align="center" style="background-color:#e70013; padding:30px 24px; color:#ffffff;">
                    <div style="font-size:26px; font-weight:700; letter-spacing:-1px;">TuniFly &#9992;</div>
                </td></tr>
                <tr><td style="padding:30px; font-size:16px; line-height:24px;">
                    <p style="margin:0 0 18px;"><strong>Good news! 🎉</strong> Your watched flight has reached your target price.</p>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fdf1f2; border-left:4px solid #e70013; border-radius:8px;"><tr><td style="padding:16px 18px;">
                        <strong style="font-size:18px; color:#c40010;">{origin} &rarr; {destination}</strong><br>
                        <span style="color:#52677d;">{escape(departure_date)} &middot; Target: {target_price:.2f}&euro;</span><br>
                        <strong style="color:#16324f;">Current price: {current_price:.2f}&euro;</strong>
                    </td></tr></table>
                </td></tr>
                {link_html}
                <tr><td align="center" style="padding:18px 24px; background-color:#102a43; color:#9db3c8; font-size:13px;">&copy; 2026 TuniFly</td></tr>
            </table>
        </td></tr></table>
    </body>
    </html>
    """

    plain_text_book_now_link = ""
    if booking_url:
        plain_text_book_now_link = f"Book Now: {booking_url}\n"

    plain_text_body = (
        f"Good news! Your watched flight has reached your target price.\n\n"
        f"Flight: {flight_details.get('originAirportCode')} -> {flight_details.get('arrivalAirportCode')}\n"
        f"Departure: {departure_date}\n"
        f"Target: {target_price:.2f} EUR\n"
        f"Current price: {current_price:.2f} EUR\n"
        f"{plain_text_book_now_link}"
        f"\n- TuniFly\n"
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
