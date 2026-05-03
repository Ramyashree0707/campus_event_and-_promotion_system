from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from db import mysql
from flask_apscheduler import APScheduler  # ✅ add this import
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Ramya'
app.config['MYSQL_PASSWORD'] = 'Ramya@0431'
app.config['MYSQL_DB'] = 'campus_events'
mysql.init_app(app)

# Scheduler config  ✅ add this
app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler()

def auto_freeze_events():
    with app.app_context():
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE events 
                SET status='frozen' 
                WHERE DATE(date) <= CURDATE() 
                AND status='approved'
            """)
            mysql.connection.commit()
            cur.close()
            print("Auto freeze done!")
        except Exception as e:
            print("Auto freeze error:", e)

scheduler.init_app(app)
scheduler.add_job(
    id='freeze_job',
    func=auto_freeze_events,
    trigger='cron',
    hour=0,
    minute=0
)
scheduler.start()

from routes.auth import auth_bp
from routes.events import events_bp
from routes.booking import booking_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(booking_bp, url_prefix='/api/booking')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/api/health')
def health():
    return {'success': True, 'message': 'Flask server is running!'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)