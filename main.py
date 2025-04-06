from flask import Flask, request, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
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

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not all(k in data for k in ("full_name", "email", "password", "phone")):
        return jsonify({"error": "Missing registration fields"}), 400

    hashed_password = generate_password_hash(data["password"])

    try:
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (full_name, email, password, phone)
                VALUES (?, ?, ?, ?)
            """, (data["full_name"], data["email"], hashed_password, data["phone"]))
            conn.commit()
        return jsonify({"message": "Registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (data["email"],))
        user = cur.fetchone()

    if user and check_password_hash(user[3], data["password"]):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "phone": user[4]
            }
        }), 200

    return jsonify({"error": "Invalid credentials"}), 400

@app.route("/report", methods=["POST"])
def submit_report():
    data = request.get_json()

    required = ["title", "description"]
    if not all(data.get(field) for field in required):
        return jsonify({"error": "Title and description are required"}), 400

    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reports (
                title, description, datetime, category, full_name,
                email, phone, location, news_link, media_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title"),
            data.get("description"),
            data.get("datetime"),
            data.get("category"),
            data.get("full_name"),
            data.get("email"),
            data.get("phone"),
            data.get("location"),
            data.get("news_link"),
            data.get("media_url")
        ))
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





