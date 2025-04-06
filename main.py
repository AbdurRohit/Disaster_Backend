from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime
import re
import html

app = Flask(__name__)

# Initialize the database
def init_db():
    with sqlite3.connect("disaster_reports.db") as conn:
        # User table for authentication
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT
            )
        """)
        
        # Reports table based on the form in the image
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                date_time TEXT NOT NULL,
                categories TEXT NOT NULL,
                location TEXT,
                location_landmark TEXT,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                news_link TEXT,
                media_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    print("Database initialized successfully.")

init_db()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(input_data):
    """Sanitize input to prevent XSS attacks"""
    if isinstance(input_data, str):
        return html.escape(input_data.strip())
    return input_data

# Register route
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Validate email format
    if not validate_email(data["email"]):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Sanitize inputs
    username = sanitize_input(data["username"])
    email = sanitize_input(data["email"])
    phone = sanitize_input(data.get("phone", ""))
    
    hashed_password = generate_password_hash(data["password"])
    
    try:
        with sqlite3.connect("disaster_reports.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password, phone) VALUES (?, ?, ?, ?)",
                (username, email, hashed_password, phone),
            )
            conn.commit()
        return jsonify({"message": "Registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# Login route
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ["email", "password"]):
        return jsonify({"error": "Email and password are required"}), 400
    
    # Sanitize email input
    email = sanitize_input(data["email"])
    
    with sqlite3.connect("disaster_reports.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
    
    if user and check_password_hash(user[3], data["password"]):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user[0],
                "username": user[1],
                "email": user[2]
            }
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 400

# Report submission route
@app.route("/report", methods=["POST"])
def submit_report():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    # Validate required fields
    if not all(key in data for key in ["title", "description"]):
        return jsonify({"error": "Report title and description are required"}), 400
    
    # Sanitize inputs
    title = sanitize_input(data.get("title"))
    description = sanitize_input(data.get("description"))
    date_time = sanitize_input(data.get("date_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    
    # Process categories (from checkboxes in the form)
    categories = []
    if "categories" in data and isinstance(data["categories"], list):
        categories = data["categories"]
    else:
        # Handle individual category fields
        category_options = ["Earthquake", "Flash Flood", "Forest Fire", "Accident", "Others"]
        for category in category_options:
            category_key = category.lower().replace(" ", "_")
            if category_key in data and data[category_key]:
                categories.append(category)
    
    categories_str = ",".join(categories) if categories else "Uncategorized"
    
    # Get other fields
    location = sanitize_input(data.get("location", ""))
    location_landmark = sanitize_input(data.get("location_landmark", ""))
    full_name = sanitize_input(data.get("full_name", ""))
    email = sanitize_input(data.get("email", ""))
    phone = sanitize_input(data.get("phone", ""))
    news_link = sanitize_input(data.get("news_link", ""))
    media_url = sanitize_input(data.get("media_url", ""))
    
    try:
        with sqlite3.connect("disaster_reports.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO reports (
                    title, description, date_time, categories, location,
                    location_landmark, full_name, email, phone, news_link, media_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, description, date_time, categories_str, location,
                location_landmark, full_name, email, phone, news_link, media_url
            ))
            conn.commit()
        return jsonify({"message": "Report submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to submit report: {str(e)}"}), 500

# Get all reports
@app.route("/reports", methods=["GET"])
def get_reports():
    try:
        with sqlite3.connect("disaster_reports.db") as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM reports ORDER BY created_at DESC")
            reports = [dict(row) for row in cur.fetchall()]
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch reports: {str(e)}"}), 500

# HTML form for report submission
@app.route("/", methods=["GET"])
def report_form():
    return render_template("report_form.html")

if __name__ == "__main__":
    app.run(debug=True)





