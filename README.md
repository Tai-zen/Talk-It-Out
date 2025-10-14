

---

# 💬 **Talk It Out – AI Emotional Companion Platform**

---
Link to hosted app: https://talk-it-out-90fw.onrender.com

### 🧠 Overview

**Talk It Out** is a warm, AI-powered mental wellness platform that lets users express themselves freely and feel genuinely heard. It’s designed to be a safe, supportive space for anyone going through tough emotions — stress, sadness, anxiety, heartbreak, loneliness — or even if you just need to chat.

This project combines advanced AI with emotional intelligence to simulate a compassionate best friend who listens without judgment. The goal is to create a therapeutic, human-like chatbot that encourages open conversation, builds emotional self-awareness, and promotes healing through connection.

Talk It Out is an innovative mental health chatbot designed specifically for students, aiming to provide accessible support and resources that promote emotional well-being. By harnessing quality data from various sources—such as open datasets, research articles, mental health organizations, and direct survey

---
## Features

- User authentication (login/signup)
- AI chat companion with memory of past conversations
- Mood tracking
- Community resources section
- Sound lounge for relaxation

### 🚀 Key Features

#### 🔐 **User Authentication**

* Secure login system with password encryption
* Session-based user tracking for personalized support
* Optional mood check on login

---

#### 💬 **AI-Powered Mental Health Chatbot**

* Acts like a supportive friend, not a therapist or robot
* Rotating mood-based tone and language (warm, poetic, playful, loving)
* Detects emotional keywords and responds with empathy
* Uses memory recall to bring up past conversations
* Avoids judgment, toxic positivity, or generic replies

---

#### 🗣️ **Voice Chat Option**

* Users can speak instead of typing
* Web Speech API converts voice to text
* Ideal for accessibility and mobile users

---

#### 📖 **Memory + Chat History**

* Remembers past facts (e.g., “you said your grandma wasn’t doing well…”)
* Stores full chat and mood history in a local SQLite database
* Shows emotional patterns and AI tone variation over time

---

#### 🧘‍♀️ **Mood Check-In System**

* Subtle mood selector before chatting
* Adjusts AI behavior based on user’s emotional state
* Adds context: sadness triggers gentle tone, joy triggers playful cheerfulness

---

---

### 🌈 Emotional Support Philosophy

**Talk It Out** isn’t trying to be a therapist. It’s a caring companion. A safe space. A listener.
It’s for:

* Late-night overthinkers
* Lonely hearts
* People who feel too much and don’t know where to put it all

TIO (the AI) uses natural language and memory to feel *real* — not sterile or scripted.

---

### 🧑‍💻 Tech Stack

| Layer       | Tech Used                         |
| ----------- | --------------------------------- |
| Frontend    | HTML, Tailwind CSS, JavaScript    |
| Backend     | Python (Flask)                    |
| Voice Input | Web Speech API                    |
| AI Engine   | OpenRouter (GPT, Claude, Mixtral) |
| Database    | SQLite (chat + mood history)      |
| Auth        | Flask session, password hashing   |
| Hosting     | Render.com                        |

---

### ⚙️ Getting Started

1. **Clone the Repository**

```bash
git clone https://github.com/your-username/talk-it-out.git
cd talk-it-out
```

2. **Set Up Environment**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the App**

```bash
python app.py
```

5. **Open in Browser**

```url
http://localhost:5000
```

---

### 🧪 Usage Example

**1. Log In**
Click “Register” to create a new user account.
Already have one? Just log in with your username and password.

**2. Start Talking**
Type (or say) whatever’s on your mind. TIO will respond like a best friend would: warmly, empathetically, and sincerely.

**Example Chat:**

> “I don’t even know why I’m crying. It’s just been a long week.”
>
> *TIO:* “Aww babe, I feel you. Sometimes emotions overflow and need a way out. Crying doesn’t mean you’re weak — it means you’re alive. I’m right here with you, okay? 💛”

---

### 🌍 Impact & Mission

Talk It Out exists to help people feel **seen**, **heard**, and **held**.
Our mission is to:

* Break emotional silence
* Encourage healing through expression
* Make AI feel more human, soft, and safe
* Empower people to open up and explore their emotions

This isn’t therapy. But it’s therapy-adjacent — a gentle step toward healing, self-reflection, and connection.

---

### 💬 Quote from the Creators

> “Everyone deserves a space to fall apart without being told to ‘stay strong.’
> Talk It Out gives you that space — soft, warm, and always there.”

---

