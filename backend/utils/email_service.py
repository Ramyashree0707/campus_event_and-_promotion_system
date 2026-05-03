# utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "shreeb0707@gmail.com"
SENDER_PASSWORD = "fbbgqugkhyqltvvd"


def send_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Your OTP - Campus Events"

        body = f"""
        Hello!

        Your OTP for Campus Events is: {otp}

        This OTP is valid for 5 minutes.
        Do not share it with anyone.
        """

        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"OTP sent to {to_email}")
        return True

    except Exception as e:
        print("EMAIL ERROR:", e)
        return False


def send_receipt_email(to_email, receipt):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = f"Booking Receipt - {receipt['event_name']}"

        body = f"""
Dear {receipt['user_name']},

Your booking is confirmed! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━
BOOKING RECEIPT
━━━━━━━━━━━━━━━━━━━━━━━━

Booking ID     : #{receipt['booking_id']}
Confirmation   : {receipt['booking_confirmation_code']}

EVENT DETAILS:
Event Name     : {receipt['event_name']}
Date           : {receipt['event_date']}
Time           : {receipt['event_time'] or 'TBD'}
Location       : {receipt['event_location']}
Amount         : {'FREE' if receipt['event_price'] == 0 else f"Rs.{receipt['event_price']}"}
Payment Status : {receipt['payment_status'].upper()}

━━━━━━━━━━━━━━━━━━━━━━━━
Present your confirmation code at the event entrance.

Thank you for booking with Campus Events!
        """

        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Receipt sent to {to_email}")
        return True

    except Exception as e:
        print("RECEIPT EMAIL ERROR:", e)
        return False