from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

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
                user_email TEXT NOT NULL
            )
        """)
    print("Database initialized successfully.")

init_db()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data["password"])

    try:
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password, phone) VALUES (?, ?, ?, ?)",
                (data["username"], data["email"], hashed_password, data.get("phone")),
            )
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
        return jsonify({"message": "Login successful"}), 200
    
    return jsonify({"error": "Invalid credentials"}), 400

@app.route("/report", methods=["POST"])
def submit_report():
    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    user_email = data.get("user_email")

    if not (title and description and user_email):
        return jsonify({"error": "Missing report fields"}), 400

    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO reports (title, description, user_email) VALUES (?, ?, ?)",
            (title, description, user_email)
        )
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



