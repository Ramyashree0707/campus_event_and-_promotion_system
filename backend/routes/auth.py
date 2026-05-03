from flask import Blueprint, request, jsonify
import jwt, datetime, random, string
from flask_bcrypt import Bcrypt
from db import mysql
from utils.email_service import send_email
from config import Config

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Store for temporary user data (until OTP verified)
temp_users = {}


def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def store_otp_in_db(email, otp):
    """Store OTP in database with 5-minute expiration"""
    try:
        cur = mysql.connection.cursor()
        # Delete old OTPs for this email
        cur.execute("DELETE FROM otp_store WHERE email=%s", (email,))
        # Insert new OTP with 5-minute expiration
        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        cur.execute("""
            INSERT INTO otp_store (email, otp_code, expires_at)
            VALUES (%s, %s, %s)
        """, (email, otp, expiration))
        mysql.connection.commit()
        cur.close()
        return True
    except Exception as e:
        print("OTP STORAGE ERROR:", e)
        return False


def verify_otp_in_db(email, otp):
    """Verify OTP from database and check expiration"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT otp_code, expires_at, used FROM otp_store
            WHERE email=%s AND used=FALSE
            ORDER BY created_at DESC LIMIT 1
        """, (email,))
        result = cur.fetchone()
        cur.close()

        if not result:
            return False

        stored_otp, expires_at, used = result

        # Check if OTP is expired
        if datetime.datetime.utcnow() > expires_at:
            return False

        # Check if OTP matches
        if stored_otp != otp:
            return False

        return True
    except Exception as e:
        print("OTP VERIFY ERROR:", e)
        return False


def mark_otp_used(email):
    """Mark OTP as used after successful verification"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE otp_store SET used=TRUE
            WHERE email=%s AND used=FALSE
        """, (email,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print("OTP MARK USED ERROR:", e)


# ================= REGISTER (SEND OTP) =================
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        print("REGISTER DATA:", data)
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "student")
        student_id = data.get("student_id")
        organizer_id = data.get("organizer_id")

        # Validation
        if not name or not email or not password:
            return jsonify({"error": "Name, email, and password are required"}), 400

        if role == "student" and not student_id:
            return jsonify({"error": "Student ID required"}), 400

        if role == "organizer" and not organizer_id:
            return jsonify({"error": "Organizer ID required"}), 400

        cur = mysql.connection.cursor()

        # Check if already exists
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            return jsonify({"error": "User already exists"}), 400

        cur.close()

        # Generate OTP
        otp = generate_otp()

        # Store OTP in database
        if not store_otp_in_db(email, otp):
            return jsonify({"error": "Failed to send OTP"}), 500

        # Store user temporarily in memory
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        temp_users[email] = {
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": role,
            "student_id": student_id if role == "student" else None,
            "organizer_id": organizer_id if role == "organizer" else None
        }

        # Send OTP via email
        send_email(email, otp)

        return jsonify({"message": "OTP sent successfully to your email"}), 200

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({"error": "Registration failed"}), 500


# ================= VERIFY REGISTER =================
@auth_bp.route("/verify-register", methods=["POST"])
def verify_register():
    try:
        data = request.get_json()

        email = data.get("email")
        otp = str(data.get("otp"))

        # Verify OTP from database
        if not verify_otp_in_db(email, otp):
            return jsonify({"error": "Invalid or expired OTP"}), 400

        # Get user data from temp storage
        user = temp_users.get(email)
        if not user:
            return jsonify({"error": "Registration session expired. Please register again."}), 400

        cur = mysql.connection.cursor()

        try:
            # Insert user into database
            cur.execute("""
                INSERT INTO users (name, email, password, role, student_id, organizer_id, verified)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """, (
                user["name"],
                user["email"],
                user["password"],
                user["role"],
                user.get("student_id"),
                user.get("organizer_id")
            ))

            mysql.connection.commit()

            # Mark OTP as used
            mark_otp_used(email)

            # Cleanup temporary data
            temp_users.pop(email, None)

            return jsonify({"message": "Registration successful! Please login."}), 200

        except Exception as e:
            mysql.connection.rollback()
            print("DB INSERT ERROR:", e)
            return jsonify({"error": "Failed to create user"}), 500
        finally:
            cur.close()

    except Exception as e:
        print("VERIFY REGISTER ERROR:", e)
        return jsonify({"error": "Verification failed"}), 500


# ================= LOGIN (SEND OTP) =================
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Verify password
        user_id, hashed_pw, role = user
        if not bcrypt.check_password_hash(hashed_pw, password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate OTP
        otp = generate_otp()

        # Store OTP in database
        if not store_otp_in_db(email, otp):
            return jsonify({"error": "Failed to send OTP"}), 500

        # Send OTP via email
        send_email(email, otp)

        return jsonify({"message": "OTP sent to your email", "user_id": user_id, "role": role}), 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"error": "Login failed"}), 500


# ================= VERIFY LOGIN =================
@auth_bp.route('/verify-login', methods=['POST'])
def verify_login():
    try:
        data = request.get_json()

        email = data.get('email')
        otp = str(data.get('otp'))

        if not email or not otp:
            return jsonify({"error": "Email and OTP required"}), 400

        # Verify OTP from database
        if not verify_otp_in_db(email, otp):
            return jsonify({"error": "Invalid or expired OTP"}), 400

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id, role = user

        # Mark OTP as used
        mark_otp_used(email)

        # Generate JWT token using Config.SECRET_KEY
        token = jwt.encode({
            "user_id": user_id,
            "email": email,
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, "campus_secret_key_2025", algorithm="HS256")

        return jsonify({
            "token": token,
            "user_id": user_id,
            "role": role,
            "message": "Login successful"
        }), 200

    except Exception as e:
        print("VERIFY LOGIN ERROR:", e)
        return jsonify({"error": "Verification failed"}), 
        # ================= VERIFY OTP (alias for frontend) =================
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    return verify_register()