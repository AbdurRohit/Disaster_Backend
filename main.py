from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                datetime TEXT,
                category TEXT,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                news_link TEXT,
                media_url TEXT
            )
        """)
    print("Database initialized")

init_db()

@app.route("/report", methods=["POST"])
def submit_report():
    data = request.get_json()

    fields = [
        "title", "description", "datetime", "category", "full_name",
        "email", "phone", "location", "news_link", "media_url"
    ]

    if not data.get("title") or not data.get("description"):
        return jsonify({"error": "Title and description are required."}), 400

    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reports (title, description, datetime, category, full_name,
                                 email, phone, location, news_link, media_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(data.get(field) for field in fields))
        conn.commit()

    return jsonify({"message": "Report submitted successfully"}), 201

@app.route("/report", methods=["GET"])
def get_reports():
    with sqlite3.connect("users.db") as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM reports")
        reports = [dict(row) for row in cur.fetchall()]

    return jsonify(reports), 200

if __name__ == "__main__":
    app.run(debug=True)




