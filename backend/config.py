# config.py
import mysql.connector

class Config:
    SECRET_KEY = "campus_secret_key_2025"  # change this to any random string
    DEBUG = True

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="Ramya",
        password="Ramya@0431",
        database="campus_events"
    )