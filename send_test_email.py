from datetime import datetime
from app.services.email_alerts import send_price_alert_email

send_price_alert_email(
    to_email="wassimsellami20@gmail.com",
    flight_details={
        "originAirportCode": "TUN",
        "arrivalAirportCode": "ORY",
        "departureDate": datetime(2026, 10, 15),
        "bookingUrl": "https://booking.nouvelair.com/ibe/availability?depPort=TUN&arrPort=ORY",
    },
    target_price=150.0,
    current_price=129.99,
)
print("Done - check logs above for SENT/FAILED status")
