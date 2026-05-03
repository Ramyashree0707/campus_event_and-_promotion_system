from flask import Blueprint, jsonify
from db import mysql

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/events', methods=['GET'])
def pending_events():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM events WHERE status='pending'")
    events = cur.fetchall()
    return jsonify(events)

@admin_bp.route('/admin/approve/<int:id>', methods=['POST'])
def approve_event(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE events SET status='approved' WHERE id=%s", (id,))
    mysql.connection.commit()
    return jsonify({"message": "Event approved"})