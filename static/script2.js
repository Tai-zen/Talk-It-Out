// 🧠 Container Switch (Login/Register)
const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

if (registerBtn) {
  registerBtn.addEventListener('click', () => {
    container.classList.add('active');
  });
}
if (loginBtn) {
  loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
  });
}

// 🍔 Sidebar Toggle
const hamburger = document.getElementById('hamburger');
const sidebar = document.getElementById('sidebar');
const closeBtn = document.getElementById('closeBtn');

if (hamburger && sidebar) {
  hamburger.addEventListener('click', () => {
    sidebar.classList.add('open');
  });
}
if (closeBtn && sidebar) {
  closeBtn.addEventListener('click', () => {
    sidebar.classList.remove('open');
  });
}

// 💬 Simple Local Chat Simulation (Optional fallback)
const chat = document.getElementById('chat');
const form = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');

if (chat && form && userInput) {
  const botReply = (input) => {
    const responses = [
      "Tell me more about that.",
      "That sounds tough. I'm here with you.",
      "How long have you been feeling this way?",
      "Have you tried any coping strategies that help?",
      "Thanks for sharing. You’re doing great by opening up."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.textContent = message;
    chat.appendChild(userMsg);

    userInput.value = '';
    chat.scrollTop = chat.scrollHeight;

    setTimeout(() => {
      const botMsg = document.createElement('div');
      botMsg.className = 'message bot';
      botMsg.textContent = botReply(message);
      chat.appendChild(botMsg);
      chat.scrollTop = chat.scrollHeight;
    }, 800);
  });
}

// 📝 Register Form Submit
const registerForm = document.getElementById('register-form');
if (registerForm) {
  registerForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const username = document.getElementById('username')?.value.trim();
    const email = document.getElementById('email')?.value.trim();
    const password = document.getElementById('password')?.value.trim();

    if (!username || !email || !password) {
      alert("Please fill in all fields");
    } else {
      window.location.href = "login.html";
    }
  });
}

// 🎵 Background Music
window.addEventListener("DOMContentLoaded", () => {
  const music = document.getElementById("bg-music");
  if (music) {
    music.volume = 0.5;
    document.body.addEventListener("click", () => {
      music.play();
      music.muted = false;
    }, { once: true });
  }
});
window.addEventListener("DOMContentLoaded", () => {
  const music = document.getElementById("bg-music");
  const playBtn = document.getElementById("play-btn");
  const muteBtn = document.getElementById("mute-btn");

  if (music) {
    music.volume = 0.5;

    // Start playing on first click if browser blocks autoplay
    document.body.addEventListener("click", () => {
      music.muted = false;
      music.play();
    }, { once: true });

    if (playBtn) {
      playBtn.addEventListener("click", () => {
        music.muted = false;
        music.play();
      });
    }

    if (muteBtn) {
      muteBtn.addEventListener("click", () => {
        music.muted = !music.muted;
        muteBtn.textContent = music.muted ? "🔇 Unmute" : "🔈 Mute";
      });
    }
  }
});
