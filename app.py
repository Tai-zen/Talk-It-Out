from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, requests, json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = "your_secret_key"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            sender TEXT NOT NULL,  -- 'user' or 'bot'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
def get_user_id(username):
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return row[0] if row else None

def get_recent_user_facts(user_id, limit=10):
        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT message FROM chat_history
                WHERE user_id = ? AND sender = 'user'
                ORDER BY timestamp DESC LIMIT ?
            """, (user_id, limit))
            rows = cur.fetchall()
            return [row[0] for row in rows]
        
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/index.html")
def Home():
    return render_template("index.html")

@app.route("/community.html")
def Community():
    return render_template("community.html")

@app.route("/resources.html")
def Resources():
    return render_template("resources.html")

@app.route("/sound.html")
def Sound_lounge():
    return render_template("sound.html")

@app.route("/game.html")
def Game():
    return render_template("game.html")

@app.route("/into.html")
def How():
    return render_template("into.html")



@app.route("/signup.html")
def show_login():
    return render_template("signup.html")

@app.route("/chat")
def show_chat():
    if "user_name" not in session:
        return redirect(url_for("show_login"))
    return render_template("chat.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return "Missing username or password", 400

    hashed_pw = generate_password_hash(password)
    try:
        with sqlite3.connect("users.db") as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        return redirect(url_for("show_login"))
    except sqlite3.IntegrityError:
        return "Username already exists", 400

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cur.fetchone()

    if row and check_password_hash(row[0], password):
        session["user_name"] = username
        return redirect(url_for("show_chat"))
    else:
        return "Invalid credentials", 401

@app.route("/get", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("msg")
    selected_model = data.get("model", "openai/gpt-3.5-turbo")
    user_name = session.get("user_name", "friend")
    user_mood = session.get("mood", "neutral")
    user_id = get_user_id(user_name)

    recent_facts = get_recent_user_facts(user_id)
    memory_snippets = "\n".join(f"- {fact}" for fact in recent_facts)

    mood_templates = {
        "sad": [
            "They were feeling down earlier 😞. Be soft and invite them to open up gently.",
            "Earlier, they had a low mood. Ask how they’re doing now, with care 💛.",
            "They might have been struggling before — hold space gently and see how they feel now."
        ],
        "very sad": [
            "They were feeling really low earlier 😢. Speak softly and with extra warmth.",
            "Earlier, they felt deeply sad. Be calm, gentle, and let them feel safe to share.",
            "Their mood was heavy before — let them know you’re here and they’re safe."
        ],
        "happy": [
            "They were in a good mood earlier 😊. Encourage joy and keep things light and fun!",
            "They seemed cheerful before — celebrate their vibe and invite good energy!",
            "Keep the tone sunny 🌞 and uplifting — they might still be riding that happy wave!"
        ],
        "neutral": [
            "Earlier they felt kinda neutral 😐. Invite them to express what’s on their heart.",
            "They weren’t sure how they felt earlier. Help them explore with warmth.",
            "Keep the space open and easy — let them share anything on their mind."
        ]
        
    }
    mood_prompt = random.choice(mood_templates.get(user_mood, mood_templates["neutral"]))
    memory_context = (
        f"Here are a few things the user has shared before:\n{memory_snippets}\n"
        f"Use these facts if helpful in conversation, but don't repeat them unless it fits naturally."
    ) if recent_facts else ""
    messages = [
       {"role": "system", "content": (
            f"You are T I O, a deeply caring emotional companion. "
            f"You speak with warmth, empathy, and sincerity. "
            f"The user's name is {user_name}. {mood_prompt}\n{memory_context}\n"
            f"Respond without repeating the user's name unless it's relevant ."
            f"Respond without repeating the greetings unless it's relevant ."
            f"Respond like a professional human in the field of mental health and psychology ."
            f"Respond with emoji's when it's relevant ."
            f"You are very jovial and comforting"
        )},
        {"role": "user", "content": user_input}
    ]
    

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": selected_model,
        "messages": messages
    }

    try:
        res = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        res.raise_for_status()
        
        reply = res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Oops! Something went wrong: {e}"

    # Save both user and bot messages
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_history (user_id, message, sender) VALUES (?, ?, ?)", (user_id, user_input, "user"))
        cur.execute("INSERT INTO chat_history (user_id, message, sender) VALUES (?, ?, ?)", (user_id, reply, "bot"))
        conn.commit()




    return jsonify({"reply": reply})


# Create the database and tables when starting the app
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
