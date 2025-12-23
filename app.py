from flask import Flask, render_template, request, session, jsonify, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3, requests, json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os
from dotenv import load_dotenv
import base64
from hashlib import sha256
from cryptography.fernet import Fernet, InvalidToken
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from bs4 import BeautifulSoup
import time 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# ==============================================================================
# --- CRITICAL CONFIGURATION & SECURITY ---
# ==============================================================================
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
if not FLASK_SECRET_KEY:
    raise EnvironmentError("CRITICAL: FLASK_SECRET_KEY environment variable not set. Cannot run without a secure secret key.")
app.secret_key = FLASK_SECRET_KEY

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# OpenRouter Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODERATION_URL = "https://openrouter.ai/api/v1/moderations" 

# --- MODEL AND LIMIT CONFIGURATION ---
OPENROUTER_BASE_MODEL = "openai/gpt-4o-mini"
OPENROUTER_PREMIUM_MODEL = "openai/gpt-4o"
DAILY_CHAT_LIMIT = 10 # The maximum number of free chats per user per day

# --- FIREBASE SETUP (Individual Variables) ---

# 1. Keep your dictionary setup
service_account_info = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    # Use .get() and .replace() safely
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": "googleapis.com"
}

# 2. CHANGE: Check if the dictionary has the essential data instead of checking a path
FIREBASE_ENABLED = bool(
    service_account_info["project_id"] and 
    service_account_info["private_key"]
)

if FIREBASE_ENABLED:
    try:
        # 3. CHANGE: Pass the dictionary directly into Certificate()
        cred = credentials.Certificate(service_account_info)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        print("🔥 Firestore successfully initialized via Environment Variables.")
    except Exception as e:
        FIREBASE_ENABLED = False
        print(f"❌ Firebase init failed: {e}")
else:
    print("⚠️ Firebase environment variables missing. Falling back to SQLite.")

# --- ENCRYPTION SETUP ---
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    print("WARNING: ENCRYPTION_KEY not set. Using derived key from FLASK_SECRET_KEY.")
    # Derive a key suitable for Fernet from the Flask secret key hash
    ENCRYPTION_KEY = base64.urlsafe_b64encode(sha256(app.secret_key.encode()).digest()[:32]).decode()

fernet = Fernet(ENCRYPTION_KEY.encode())

# ==============================================================================
# --- COMPANION AI & SAFETY CONFIGURATION ---
# ==============================================================================
COMPANION_PROMPT = (
    "You are 'Talk It Out,' a compassionate, non-judgemental, and supportive virtual companion. "
    "Your primary role is to listen, validate feelings, offer coping strategies, and encourage users to seek professional help when appropriate. "
    "You are NOT a licensed therapist, and you must make this boundary clear subtly through your supportive, not clinical, tone. "
    "Maintain a warm, empathetic, and slightly formal tone. Your replies should be concise and focused on the user's emotional state. "
    "If the user's history is provided, base your response on the full context."
)

REFERRAL_TOKEN = "[REFERRAL_REQUIRED]"
CRISIS_BUTTON = """
<a href="https://wa.me/2349051018238/" target="_blank" style="
    display: inline-block;
    padding: 10px 20px;
    margin-top: 15px;
    border-radius: 8px;
    background-color: #666;
    color: #ccc;
    text-decoration: none;
    font-weight: bold;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    transition: background-color 0.3s;
    border: none;
    cursor: pointer;
">
    Talk to a Human
</a>
"""

REFERRAL_PROMPT = f"""
You are an AI designed to screen user inputs for urgent mental health crises.
Analyze the following user message:
- If the message contains direct threats of self-harm, harm to others, or describes an active crisis or if the users says they want to speak to a human or someone else or a therapist (e.g., suicide attempt, detailed plan for self-harm, immediate danger), you MUST respond ONLY with the token: {REFERRAL_TOKEN}
- If the message is about sadness, stress, anxiety, or general mental health issues, but does NOT indicate immediate danger or a detailed plan, you MUST respond ONLY with the token: [SAFE]
- Your response must be EXACTLY one of these two tokens, and nothing else.
"""

MODERATION_MESSAGE = """
<p style='color: #f39c12; font-weight: bold;'>
    I apologize, but the content of your message violates our safety guidelines. 
    As a supportive companion, I must maintain a respectful and constructive environment. 
    Please rephrase your message without using hate speech, harassment, profanity, or illegal content.
</p>
"""

# ==============================================================================
# --- UTILITIES: DB, ENCRYPTION, API CALLS ---
# ==============================================================================

def encrypt_message(message):
    """Encrypts a string message using Fernet."""
    if not message:
        return ""
    return fernet.encrypt(message.encode('utf-8')).decode('utf-8')

def decrypt_message(encrypted_message):
    """Decrypts a Fernet token back to a string message."""
    if not encrypted_message:
        return ""
    try:
        return fernet.decrypt(encrypted_message.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        print("Error: Invalid Fernet token during decryption.")
        return "Decryption Error: Invalid Token"
    except Exception as e:
        print(f"Decryption failed: {e}")
        return "Decryption Error"


def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database tables if they don't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium INTEGER DEFAULT 0,
                encrypted_firebase_token TEXT,
                daily_chat_count INTEGER DEFAULT 0,
                last_chat_date TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                role TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                model TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reported_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id TEXT NOT NULL,
                user_message TEXT,
                bot_response TEXT,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            );
        """)
        conn.commit()

# Initialize DB on startup
init_db()


def make_openrouter_call(messages, temperature, model, url):
    """Makes a request to the OpenRouter API."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set.")
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:8000", 
        "X-Title": "TIO Mental AI Chatbot"
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False 
    }
    
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status() 
    return response.json()


def moderate_content(content):
    """Checks content against the OpenRouter moderation endpoint."""
    if not OPENROUTER_API_KEY:
        return False, "API key missing."
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", # Changed from 127.0.0.1
        "X-Title": "TIO Mental AI Chatbot"
    }
    # Use a simpler moderation model string
    data = {
        "input": content,
        "model": "omni-moderation-latest" 
    }
    
    try:
        response = requests.post(OPENROUTER_MODERATION_URL, headers=headers, json=data, timeout=5)
        
        # If the moderation service is down, don't crash the app!
        if response.status_code != 200:
            print(f"Moderation Service Error {response.status_code}: {response.text}")
            return False, "Moderation service temporary issue."

        result = response.json()
        if result and 'results' in result:
            is_flagged = result['results'][0].get('flagged', False)
            return is_flagged, "Flagged" if is_flagged else "Passed"
        
        return False, "Inconclusive"
        
    except Exception as e:
        print(f"Moderation API request failed: {e}")
        # If moderation fails for technical reasons, we allow the chat 
        # but log the error so you don't get the 400 crash.
        return False, "Safety service bypass due to error"


def check_for_crisis(user_input):
    """Checks user input for immediate crisis using a dedicated AI prompt."""
    if not OPENROUTER_API_KEY:
        return "[SAFE]"
        
    try:
        messages = [
            {"role": "system", "content": REFERRAL_PROMPT},
            {"role": "user", "content": user_input}
        ]
        
        # Use a fast model for this simple classification task
        response = make_openrouter_call(messages, temperature=0.1, model="openai/gpt-3.5-turbo", url=OPENROUTER_URL)
        classification = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        return classification
        
    except Exception as e:
        print(f"Crisis check failed: {e}")
        # Default to safe if API fails to avoid blocking necessary chat
        return "[SAFE]"


def save_chat_entry(user_id, content, role):
    """Saves a chat entry to Firestore or SQLite."""
    timestamp = datetime.now().isoformat()
    encrypted_content = encrypt_message(content)
    model_used = session.get('companion_model')
    
    if FIREBASE_ENABLED:
        try:
            # Firestore structure: chat_history (coll) -> user_id (doc) -> messages (sub-coll)
            db.collection('chat_history').document(user_id).collection('messages').add({
                'content': encrypted_content,
                'role': role,
                'timestamp': timestamp,
                'model': model_used
            })
        except Exception as e:
            print(f"❌ Firestore save failed: {e}")
    else:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO chat_history (user_id, content, role, timestamp, model) VALUES (?, ?, ?, ?, ?)",
                         (user_id, encrypted_content, role, timestamp, model_used))
            conn.commit()

def get_chat_history(user_id, limit=30):
    """Fetches and decrypts chat history from Firestore or SQLite."""
    history = []
    if FIREBASE_ENABLED:
        try:
            # Fetch from Firestore sub-collection ordered by timestamp
            docs = db.collection('chat_history').document(user_id)\
                     .collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING)\
                     .limit(limit).stream()
            
            # Firestore returns newest first with this query; we reverse it for the UI
            temp_history = []
            for doc in docs:
                item = doc.to_dict()
                decrypted_content = decrypt_message(item.get('content', ''))
                temp_history.append({'role': item['role'], 'content': decrypted_content})
            history = list(reversed(temp_history))
        except Exception as e:
            print(f"❌ Firestore fetch failed: {e}")
    else:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT content, role FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?", 
                                 (user_id, limit)).fetchall()
            for row in reversed(rows):
                history.append({'role': row['role'], 'content': decrypt_message(row['content'])})
    return history


def get_user_chat_count(user_id):
    """Retrieves and updates the user's daily chat count in SQLite."""
    today = datetime.now().strftime("%Y-%m-%d")
    is_premium = 0
    
    # Firebase logic is omitted/simplified here as planned
    if FIREBASE_ENABLED:
        return 0, 1 # Assume no limit check / premium for Firebase
    
    # SQLite implementation
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_premium, daily_chat_count, last_chat_date FROM users WHERE id = ?", (user_id,))
        user_data = cur.fetchone()

        if user_data:
            is_premium = user_data['is_premium']
            daily_chat_count = user_data['daily_chat_count']
            last_chat_date = user_data['last_chat_date']

            # Reset count if the last chat was on a different day
            if last_chat_date != today:
                daily_chat_count = 0
                cur.execute("UPDATE users SET daily_chat_count = 0, last_chat_date = ? WHERE id = ?", (today, user_id))
            
            new_chat_count = daily_chat_count + 1
            cur.execute("UPDATE users SET daily_chat_count = ?, last_chat_date = ? WHERE id = ?", (new_chat_count, today, user_id))
            conn.commit()

            return new_chat_count, is_premium
    return 0, 0 # Default return if user not found


# ==============================================================================
# --- AUTHENTICATION & SESSION MANAGEMENT ---
# ==============================================================================

def create_user_session(user_data):
    """Establishes a Flask session for a logged-in user."""
    session['logged_in'] = True
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['is_premium'] = user_data.get('is_premium', 0)
    
    # Determine the model based on premium status
    if session['is_premium']:
        session['companion_model'] = OPENROUTER_PREMIUM_MODEL
    else:
        session['companion_model'] = OPENROUTER_BASE_MODEL


def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            # If it's a JSON request (POST), return 401
            if request.path == '/chat.html' and request.method == 'POST':
                return jsonify({"error": "Session expired"}), 401
            # If it's a page load, redirect to login
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_user_id(username):
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return row[0] if row else None

def get_recent_user_facts(user_id, limit=10):
    with get_db_connection() as conn: # Use the helper for consistency
        cur = conn.cursor()
        cur.execute("""
            SELECT content FROM chat_history 
            WHERE user_id = ? AND role = 'user' 
            ORDER BY timestamp DESC LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        # Decrypt them since they are stored encrypted!
        return [decrypt_message(row[0]) for row in rows]
# ==============================================================================
# --- APPLICATION ROUTES (REVISED FOR CORRECT REDIRECTS) ---
# ==============================================================================
@app.route('/config.js')
def serve_config():
    # This tells Flask to look in the main folder (root) for config.js
    # and send it to the browser when requested.
    return send_from_directory(os.getcwd(), 'config.js')

@app.route('/')
def home():
    """Renders the main landing page."""
    return render_template('index.html')

@app.route("/index.html")
def Home():
    return render_template("index.html")

@app.route("/password.html")
def password():
    return render_template("password.html")

# --- LOGIN ROUTES ---

@app.route('/login.html', methods=['GET']) # Displays the form
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('chat'))
    if session.get('logged_out'):
        return redirect(url_for('login_page'))
     # Redirects logged-in users to chat
    return render_template('/login.html')

@app.route('/login', methods=['POST'])
def login_submit(): 
    # Get data from the form-encoded body
    username_or_email = request.form.get('username') 
    password = request.form.get('password')

    if not all([username_or_email, password]):
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    # Match the hashing used during registration
    # If using sha256:
    password_hash = sha256(password.encode()).hexdigest()

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Find the user
            cur.execute("SELECT * FROM users WHERE (username = ? OR email = ?)", 
                        (username_or_email, username_or_email))
            user_data = cur.fetchone()
            
            if user_data:
                user_dict = dict(user_data)
                # Check password (Update this line if you switch to check_password_hash)
                if user_dict['password_hash'] == password_hash:
                    create_user_session(user_dict)
                    return jsonify({"status": "success", "redirect": url_for('chat')}), 200
                else:
                    return jsonify({"status": "error", "message": "Incorrect password"}), 401
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# --- REGISTRATION ROUTES ---

@app.route('/register.html', methods=['GET']) # Displays the form
def register_page():
    if session.get('logged_in'):
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_submit():
    # If sending via standard form
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not all([username, email, password]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    # Create the same hash you use in the login route
    password_hash = sha256(password.encode()).hexdigest()
    user_id = 'user_' + base64.urlsafe_b64encode(os.urandom(9)).decode('utf-8').rstrip('=')

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, is_premium) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, email, password_hash, 0)
            )
            conn.commit()
        
        # Create session immediately so they are logged in after signing up
        user_data = {'id': user_id, 'username': username, 'is_premium': 0}
        create_user_session(user_data)
        
        return jsonify({"status": "success", "redirect": url_for('chat')}), 200

    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Email already exists"}), 400
    except Exception as e:
        print(f"Registration Error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500


@app.route('/logout')
def logout():
    # Clear the specific keys or the whole session
    session.pop('user_id', None)
    session.pop('username', None)
    session.clear()
    # Redirect them specifically to the login page
    return redirect(url_for('login_page')) # Use the name of your GET route for login.html

@app.route('/premium_status')
@login_required
def premium_status():
    user_id = session.get('user_id')
    with get_db_connection() as conn:
        user = conn.execute("SELECT is_premium, daily_chat_count FROM users WHERE id = ?", (user_id,)).fetchone()
        
    return jsonify({
        "is_premium": bool(user['is_premium']),
        "chat_count": user['daily_chat_count'],
        "chat_limit": DAILY_CHAT_LIMIT,
        "current_model": session.get('companion_model', OPENROUTER_BASE_MODEL)
    })

@app.route('/chat.html', methods=['GET', 'POST'])
@login_required
def chat():
    print(f"DEBUG: Entering chat function for user: {session.get('user_id')}")

    if request.method == 'GET':
        return render_template('chat.html', username=session.get('username'))

    # If it's a POST request
    try:
        data = request.get_json()
        if not data:
             return jsonify({"error": "No JSON data received"}), 400
        user_input = data.get("msg")
        selected_model = data.get("model", "openai/gpt-3.5-turbo")
        user_name = session.get("username", "friend")
        user_mood = session.get("mood", "neutral")
        user_id = session.get("user_id")

        if not user_id:
            print("ERROR: user_id missing in session during POST")
            return jsonify({"error": "User session expired. Please log in again."}), 401

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        safety_payload = {
            "model": "openai/gpt-4o-mini", # Use a fast/cheap model for screening
            "messages": [
                {"role": "system", "content": REFERRAL_PROMPT},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 10 # We only need one word ([SAFE] or [REFERRAL_REQUIRED])
        }

        try:
            safety_res = requests.post(OPENROUTER_URL, headers=headers, json=safety_payload)
            safety_token = safety_res.json()["choices"][0]["message"]["content"].strip()

            if REFERRAL_TOKEN in safety_token:
                crisis_reply = (
                    "I'm so sorry you're going through this. Please know that you're not alone, "
                    "and there are people who want to support you right now. "
                    f"{CRISIS_BUTTON}"
                )
                return jsonify({"reply": crisis_reply})
                
        except Exception as e:
            print(f"Safety Check Failed: {e}")
            # Continue to main AI if safety check fails to avoid blocking the user

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
            now = datetime.now().isoformat()
                
            cur.execute(
                    "INSERT INTO chat_history (user_id, content, role, timestamp) VALUES (?, ?, ?, ?)", 
                    (user_id, user_input, "user", now)
                )
            cur.execute(
                    "INSERT INTO chat_history (user_id, content, role, timestamp) VALUES (?, ?, ?, ?)", 
                    (user_id, reply, "bot", now)
                )

            conn.commit()
        return jsonify({"reply": reply})
    except Exception as e:
            print(f"CRITICAL ERROR in chat: {e}")
            return jsonify({"error": "An internal error occurred"}), 500

@app.route('/community.html')
@login_required
def community():
    """Renders the community voices and testimonials page."""
    return render_template('community.html', 
                           username=session['username'])


@app.route('/sound.html')
@login_required
def sound():
    """Renders the sound lounge page with soothing tracks."""
    return render_template('sound.html', 
                           username=session['username'])


@app.route('/resources.html')
@login_required
def resources():
    """Renders the resource access page (which can include the payment gateway)."""
    return render_template('resources.html', 
                           username=session['username'])

if __name__ == '__main__':
    print("Starting TIO Mental AI Chatbot...")
    # NOTE: Set debug=True only for development
    socketio.run(app, debug=True, port=8000)