from flask import Flask, request, jsonify, render_template 
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
DATABASE = "lost_and_found.db"

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                is_lost INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
    print("Database initialized.")

# Initialize the database
init_db()

# API Routes

# Home route
@app.route('/')
def home():
    return "Welcome to the Lost & Found Community Hub!"

# Register user
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
            conn.commit()
            return jsonify({"message": "User registered successfully"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Email already exists"}), 400

# Post an item
@app.route('/post_item', methods=['POST'])
def post_item():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    location = data.get('location')
    is_lost = data.get('is_lost')  # 1 for lost, 0 for found
    user_id = data.get('user_id')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO items (title, description, location, is_lost, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, location, is_lost, user_id))
        conn.commit()
        return jsonify({"message": "Item posted successfully"}), 201

# Search items
@app.route('/search_items', methods=['GET'])
def search_items():
    query = request.args.get('query', '')
    is_lost = request.args.get('is_lost')  # Optional filter
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        if is_lost:
            cursor.execute("""
                SELECT items.*, users.name, users.email 
                FROM items 
                JOIN users ON items.user_id = users.id 
                WHERE (title LIKE ? OR description LIKE ? OR location LIKE ?) 
                AND is_lost = ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", is_lost))
        else:
            cursor.execute("""
                SELECT items.*, users.name, users.email 
                FROM items 
                JOIN users ON items.user_id = users.id 
                WHERE title LIKE ? OR description LIKE ? OR location LIKE ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        results = cursor.fetchall()
        items = [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "location": row[3],
                "is_lost": bool(row[4]),
                "timestamp": row[5],
                "user": {"name": row[6], "email": row[7]}
            } for row in results
        ]
        return jsonify(items), 200

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

