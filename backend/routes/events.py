from time import time

from flask import Blueprint, request, jsonify
import MySQLdb
import jwt as pyjwt

def get_db():
    return MySQLdb.connect(
        host="localhost",
        user="Ramya",
        passwd="Ramya@0431",
        db="campus_events"
    )

def get_current_user():
    try:
        auth_header = request.headers.get('Authorization')
        print("AUTH HEADER:", auth_header)        # ← debug line
        if not auth_header or not auth_header.startswith('Bearer '):
            print("NO TOKEN FOUND")               # ← debug line
            return None
        token = auth_header.split(' ')[1]
        decoded = pyjwt.decode(token, "campus_secret_key_2025", algorithms=["HS256"])
        print("DECODED TOKEN:", decoded)           # ← debug line
        return decoded
    except Exception as e:
        print("Token decode error:", e)
        return None

events_bp = Blueprint('events', __name__)


# GET promoted/featured events
@events_bp.route('/promoted', methods=['GET'])
def get_promoted_events():
    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT e.*, u.name as organizer_name 
            FROM events e JOIN users u ON e.organizer_id = u.id
            WHERE e.status = 'approved' AND e.is_featured = 1
            ORDER BY e.date ASC LIMIT 10
        """)
        events = cursor.fetchall()
        for event in events:
            if event.get('date'):
                event['date'] = str(event['date'])
        cursor.close()
        db.close()
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# GET upcoming events
@events_bp.route('/upcoming', methods=['GET'])
def get_upcoming_events():
    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT e.*, u.name as organizer_name 
            FROM events e JOIN users u ON e.organizer_id = u.id
            WHERE e.status = 'approved' AND e.date >= CURDATE()
            ORDER BY e.date ASC LIMIT 10
        """)
        events = cursor.fetchall()
        for event in events:
            if event.get('date'):
                event['date'] = str(event['date'])
        cursor.close()
        db.close()
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# GET all events (public)
@events_bp.route('/', methods=['GET'])
def get_events():
    try:
        category = request.args.get('category')
        date = request.args.get('date')
        search = request.args.get('search')

        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)

        query = """SELECT e.*, u.name as organizer_name 
                   FROM events e JOIN users u ON e.organizer_id = u.id
                   WHERE e.status = 'approved'"""
        params = []

        if category:
            query += ' AND e.category = %s'
            params.append(category)
        if date:
            query += ' AND DATE(e.date) = %s'
            params.append(date)
        if search:
            query += ' AND (e.name LIKE %s OR e.description LIKE %s)'
            params.extend([f'%{search}%', f'%{search}%'])

        query += ' ORDER BY e.date ASC'
        cursor.execute(query, params)
        events = cursor.fetchall()
        for event in events:
            if event.get('date'):
                event['date'] = str(event['date'])
        cursor.close()
        db.close()
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# GET organizer's own events
@events_bp.route('/my', methods=['GET'])
def my_events():
    try:
        current_user = get_current_user()
        print("CURRENT USER:", current_user)  # debug
        if not current_user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        if current_user['role'] not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        
        # ✅ No JOIN — direct query
        cursor.execute(
            'SELECT * FROM events WHERE organizer_id = %s ORDER BY id DESC',
            (current_user['user_id'],)
        )
        events = cursor.fetchall()
        print("EVENTS FOUND:", len(events))  # debug
        for event in events:
            if event.get('date'):
                event['date'] = str(event['date'])
        cursor.close()
        db.close()
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        print("MY EVENTS ERROR:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

# GET single event (public)
@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """SELECT e.*, u.name as organizer_name FROM events e
               JOIN users u ON e.organizer_id = u.id WHERE e.id = %s""",
            (event_id,)
        )
        event = cursor.fetchone()
        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        if event.get('date'):
            event['date'] = str(event['date'])
        cursor.close()
        db.close()
        return jsonify({'success': True, 'event': event})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# POST create event (organizer only)
@events_bp.route('/', methods=['POST'])
def create_event():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        if current_user['role'] not in ['organizer', 'admin']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        date = data.get('date')
        venue = data.get('venue')
        time = data.get('time')   
        price = data.get('price', 0)
        total_seats = data.get('total_seats')
        category = data.get('category', 'Fest')
        image_url = data.get('image_url')

        if not all([name, date, venue, total_seats]):
            return jsonify({'success': False, 'message': 'Required fields missing'}), 400

        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """INSERT INTO events (name, description, date,time, venue, price, total_seats,
               available_seats, category, image_url, organizer_id, status)
               VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, 'approved')""",
            (name, description, date, time,venue, price, total_seats,
             total_seats, category, image_url, current_user['user_id'])
        )
        db.commit()
        event_id = cursor.lastrowid
        cursor.close()
        db.close()
        return jsonify({'success': True, 'message': 'Event created!', 'eventId': event_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# PUT update event
@events_bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
        event = cursor.fetchone()

        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        if current_user['role'] != 'admin' and event['organizer_id'] != current_user['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        data = request.get_json()
        cursor.execute(
            """UPDATE events SET name=%s, description=%s, date=%s, venue=%s,
               price=%s, total_seats=%s, category=%s, image_url=%s,
               is_featured=%s, is_trending=%s, status=%s WHERE id=%s""",
            (
                data.get('name', event['name']),
                data.get('description', event['description']),
                data.get('date', event['date']),
                data.get('venue', event['venue']),
                data.get('price', event['price']),
                data.get('total_seats', event['total_seats']),
                data.get('category', event['category']),
                data.get('image_url', event['image_url']),
                data.get('is_featured', event['is_featured']),
                data.get('is_trending', event['is_trending']),
                data.get('status', event['status']),
                event_id
            )
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'success': True, 'message': 'Event updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# DELETE event
@events_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        db = get_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
        event = cursor.fetchone()

        if not event:
            return jsonify({'success': False, 'message': 'Event not found'}), 404
        if current_user['role'] != 'admin' and event['organizer_id'] != current_user['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        # ✅ Delete bookings first before deleting event
        cursor.execute('DELETE FROM bookings WHERE event_id = %s', (event_id,))

        # ✅ Now delete the event
        cursor.execute('DELETE FROM events WHERE id = %s', (event_id,))

        db.commit()
        cursor.close()
        db.close()
        return jsonify({'success': True, 'message': 'Event deleted'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500