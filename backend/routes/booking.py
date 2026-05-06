from flask import Blueprint, request, jsonify
from utils.email_service import send_receipt_email

from db import mysql
import MySQLdb.cursors
import random
import string
import datetime

booking_bp = Blueprint('booking', __name__)


def generate_confirmation_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ================= STEP 1: CHECK BEFORE PAYMENT =================
@booking_bp.route('/book', methods=['POST'])
def book():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        event_id = data.get('event_id')

        if not user_id or not event_id:
            return jsonify({"error": "user_id and event_id required"}), 400

        cur = mysql.connection.cursor()

        # Check if already booked
        cur.execute("""
            SELECT id FROM bookings
            WHERE user_id=%s AND event_id=%s AND status='completed'
        """, (user_id, event_id))

        if cur.fetchone():
            cur.close()
            return jsonify({"error": "You have already booked this event"}), 400

        # Get event details
        cur.execute("""
            SELECT id, name, price, available_seats, total_seats
            FROM events
            WHERE id=%s AND status='approved'
        """, (event_id,))

        event = cur.fetchone()
        cur.close()

        if not event:
            return jsonify({"error": "Event not found"}), 404

        event_id, event_name, price, available_seats, total_seats = event

        if available_seats <= 0:
            return jsonify({"error": "No seats available", "status": "SOLD_OUT"}), 400

        return jsonify({
            "message": "Booking check passed",
            "event_id": event_id,
            "event_name": event_name,
            "price": price,
            "available_seats": available_seats,
            "action": "PROCEED_TO_PAYMENT" if price > 0 else "DIRECT_BOOKING"
        }), 200

    except Exception as e:
        print("BOOK CHECK ERROR:", e)
        return jsonify({"error": "Booking check failed"}), 500


# ================= STEP 2: CONFIRM BOOKING (Free Event) =================
@booking_bp.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        event_id = data.get('event_id')

        if not user_id or not event_id:
            return jsonify({"error": "user_id and event_id required"}), 400

        cur = mysql.connection.cursor()

        try:
            # Check if already booked ✅ one booking per student per event
            cur.execute("""
                SELECT id FROM bookings
                WHERE user_id=%s AND event_id=%s AND status='completed'
            """, (user_id, event_id))

            if cur.fetchone():
                cur.close()
                return jsonify({"error": "You have already booked this event"}), 400

            # Re-check availability
            cur.execute("""
                SELECT id, available_seats, price
                FROM events WHERE id=%s AND status='approved'
            """, (event_id,))

            event = cur.fetchone()

            if not event:
                cur.close()
                return jsonify({"error": "Event not found"}), 404

            event_id_check, available_seats, price = event

            if available_seats <= 0:
                cur.close()
                return jsonify({"error": "No seats available"}), 400

            confirmation_code = generate_confirmation_code()

            # Create booking
            cur.execute("""
                INSERT INTO bookings
                (user_id, event_id, status, payment_status, booking_confirmation_code)
                VALUES (%s, %s, 'completed', %s, %s)
            """, (
                user_id, event_id,
                'free' if price == 0 else 'paid',
                confirmation_code
            ))

            booking_id = cur.lastrowid

            # Reduce available seats ✅ fixed column name
            cur.execute("""
                UPDATE events SET available_seats = available_seats - 1
                WHERE id=%s
            """, (event_id,))

            mysql.connection.commit()

            return jsonify({
                "message": "Booking confirmed",
                "booking_id": booking_id,
                "confirmation_code": confirmation_code,
                "status": "COMPLETED"
            }), 200

        except Exception as e:
            mysql.connection.rollback()
            raise e
        finally:
            cur.close()

    except Exception as e:
        print("CONFIRM BOOKING ERROR:", e)
        return jsonify({"error": "Booking confirmation failed"}), 500


# ================= STEP 3: CONFIRM BOOKING AFTER PAYMENT =================
@booking_bp.route('/confirm-payment', methods=['POST'])
def confirm_payment():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        event_id = data.get('event_id')
        payment_method = data.get('payment_method', 'unknown')

        if not user_id or not event_id:
            return jsonify({"error": "user_id and event_id required"}), 400

        cur = mysql.connection.cursor()

        try:
            # Check if already booked ✅ one booking per student per event
            cur.execute("""
                SELECT id FROM bookings
                WHERE user_id=%s AND event_id=%s AND status='completed'
            """, (user_id, event_id))

            if cur.fetchone():
                cur.close()
                return jsonify({"error": "You have already booked this event"}), 400

            # Re-check availability
            cur.execute("""
                SELECT id, available_seats FROM events
                WHERE id=%s AND status='approved'
            """, (event_id,))

            event = cur.fetchone()

            if not event:
                cur.close()
                return jsonify({"error": "Event not found"}), 404

            event_id_check, available_seats = event

            if available_seats <= 0:
                cur.close()
                return jsonify({"error": "No seats available"}), 400

            confirmation_code = generate_confirmation_code()

            # Create booking
            cur.execute("""
                INSERT INTO bookings
                (user_id, event_id, status, payment_status, booking_confirmation_code)
                VALUES (%s, %s, 'completed', 'paid', %s)
            """, (user_id, event_id, confirmation_code))

            booking_id = cur.lastrowid

            # Reduce available seats ✅ fixed column name
            cur.execute("""
                UPDATE events SET available_seats = available_seats - 1
                WHERE id=%s
            """, (event_id,))

            mysql.connection.commit()

            return jsonify({
                "message": "Payment confirmed and booking created",
                "booking_id": booking_id,
                "confirmation_code": confirmation_code,
                "status": "COMPLETED"
            }), 200

        except Exception as e:
            mysql.connection.rollback()
            raise e
        finally:
            cur.close()

    except Exception as e:
        print("CONFIRM PAYMENT ERROR:", e)
        return jsonify({"error": "Payment confirmation failed"}), 500


# ================= GET USER'S BOOKINGS =================
@booking_bp.route('/my-bookings', methods=['GET'])
def get_my_bookings():
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT b.id, b.user_id, b.event_id, b.booking_date,
                   b.status, b.payment_status, b.booking_confirmation_code,
                   e.name as event_name, e.date, e.time, e.venue, e.price
            FROM bookings b
            JOIN events e ON b.event_id = e.id
            WHERE b.user_id=%s
            ORDER BY b.booking_date DESC
        """, (user_id,))

        bookings = cur.fetchall()
        cur.close()
        return jsonify(bookings), 200

    except Exception as e:
        print("GET BOOKINGS ERROR:", e)
        return jsonify({"error": "Failed to fetch bookings"}), 500


# ================= GET RECEIPT =================
@booking_bp.route('/bookings/<int:booking_id>/receipt', methods=['GET'])
def get_receipt(booking_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT b.id as booking_id, b.user_id, b.booking_date,
                   b.booking_confirmation_code, b.payment_status,
                   u.name as user_name, u.email as user_email,
                   e.id as event_id, e.name as event_name,
                   e.date as event_date, e.time as event_time,
                   e.venue as event_location, e.price as event_price
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN events e ON b.event_id = e.id
            WHERE b.id=%s
        """, (booking_id,))

        receipt = cur.fetchone()
        cur.close()

        if not receipt:
            return jsonify({"error": "Booking not found"}), 404

        return jsonify(receipt), 200

    except Exception as e:
        print("GET RECEIPT ERROR:", e)
        return jsonify({"error": "Failed to fetch receipt"}), 500


# ================= SEND RECEIPT VIA EMAIL =================
@booking_bp.route('/send-receipt', methods=['POST'])
def send_receipt():
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        user_email = data.get('user_email')

        if not booking_id or not user_email:
            return jsonify({"error": "booking_id and user_email required"}), 400

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT b.id as booking_id, b.booking_confirmation_code,
                   b.payment_status, u.name as user_name,
                   e.name as event_name, e.date as event_date,
                   e.time as event_time, e.venue as event_location,
                   e.price as event_price
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN events e ON b.event_id = e.id
            WHERE b.id=%s
        """, (booking_id,))

        receipt = cur.fetchone()
        cur.close()

        if not receipt:
            return jsonify({"error": "Booking not found"}), 404

        # ✅ actually send email
        success = send_receipt_email(user_email, receipt)

        if success:
            return jsonify({"message": "Receipt sent to email!"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500

    except Exception as e:
        print("SEND RECEIPT ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ================= CANCEL BOOKING =================
@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
def cancel_booking(booking_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, event_id, status FROM bookings WHERE id=%s", (booking_id,))
        booking = cur.fetchone()

        if not booking:
            cur.close()
            return jsonify({"error": "Booking not found"}), 404

        user_id, event_id, status = booking

        if status == 'cancelled':
            cur.close()
            return jsonify({"error": "Booking already cancelled"}), 400

        cur.execute("UPDATE bookings SET status='cancelled' WHERE id=%s", (booking_id,))

        # Restore seat ✅ fixed column name
        cur.execute("""
            UPDATE events SET available_seats = available_seats + 1
            WHERE id=%s
        """, (event_id,))

        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Booking cancelled successfully"}), 200

    except Exception as e:
        print("CANCEL BOOKING ERROR:", e)
        return jsonify({"error": "Failed to cancel booking"}), 500