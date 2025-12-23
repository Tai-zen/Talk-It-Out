  // Import the functions you need from the SDKs you use
  import { initializeApp } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-app.js";
  import { getAuth, signOut } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-auth.js";
// Your web app's Firebase configuration
  import { firebaseConfig } from './config.js';

// Now use firebaseConfig.apiKey etc.
    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    export { app, auth };


  window.send = function() {
const inputField = document.getElementById("userInput");
    const chat = document.getElementById("chatbox");
    
    // Safety check to ensure the elements exist
    if (!inputField || !chat) {
        console.error("Critical UI elements missing!");
        return;
    }

    const input = inputField.value.trim();
    if (!input) return;
    // Append user message
    chat.innerHTML += `<div class="message user">${input}</div>`;

    fetch("/chat.html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ msg: input})
    })
    .then(res => res.text()) 
    .then(text => {
      console.log("Response from server:", text); // Debug output
      let data;
      try {
        data = JSON.parse(text);  
      } catch (e) {
        console.error("Failed to parse JSON:", e);
        data = { reply: "Sorry, I couldn't understand the response." }; // Fallback message
      }
      const reply = data.reply || data.message || data; 
      chat.innerHTML += `<div class="message bot">${reply}</div>`;
      document.getElementById("userInput").value = "";
      chat.scrollTop = chat.scrollHeight;
    })
    .catch(error => {
      console.error("Fetch error:", error);
      // Optional: Show a user-friendly message
      chat.innerHTML += `<div class="message bot">Sorry, there was an error processing your request.</div>`;
      document.getElementById("userInput").value = "";
    });
  }
    /** Updates the chat header with model and limit status. */
    window.updateChatHeader= function(data) {
        const chatHeader = document.querySelector('.chat-header');
        // Clear previous status elements
        chatHeader.innerHTML = '🧠 T I O - Talk It Out'; 
        
        const statusSpan = document.createElement('span');
        statusSpan.style.marginLeft = '15px';
        statusSpan.style.fontSize = '0.9rem';
        statusSpan.style.fontWeight = 'normal';
        
        let statusText = '';
        if (data.is_premium) {
            statusText = `Premium: ${data.current_model} (Unlimited)`;
            statusSpan.style.color = '#2ecc71'; // Green
        } else {
            const chatsLeft = data.chat_limit - data.chat_count;
            statusText = `Free: ${data.current_model} (${chatsLeft}/${data.chat_limit} left)`;
            statusSpan.style.color = chatsLeft > 0 ? '#f39c12' : '#e74c3c'; // Yellow/Red
        }
        
        statusSpan.textContent = statusText;
        chatHeader.appendChild(statusSpan);
    }
    
    // --- API & State Functions ---

    /** Fetches and updates the user's premium status and limits. */
    function fetchPremiumStatus() {
        fetch("/premium_status")
            .then(res => res.json())
            .then(data => {
                updateChatHeader(data);
            })
            .catch(error => console.error("Error fetching premium status:", error));
    }
    
    /** Simulates opening and processing a premium payment modal. */
    function showPremiumModal() {
        alert("This is a simulated payment flow for the Premium Chat access. Proceeding with simulation...");
        fetch('/create_checkout_session', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    fetchPremiumStatus(); // Refresh status
                } else {
                    alert("Payment simulation failed: " + data.message);
                }
            })
            .catch(err => alert("Error during simulated payment: " + err));
    }
    // --- Reporting Feature Logic ---

    window.reportLastMessage = function() {
        const messages = document.querySelectorAll('#chatbox > .message');
        if (messages.length < 2) {
            alert("Need at least one user message and one bot reply to report.");
            return;
        }

        const lastBotMessage = messages[messages.length - 1];
        const lastUserMessage = messages[messages.length - 2];
        
        if (lastBotMessage.classList.contains('bot') && lastUserMessage.classList.contains('user')) {
             const userMsg = lastUserMessage.textContent;
             
             // Extract plain text from bot reply, removing HTML elements like buttons
             const botReplyContainer = document.createElement('div');
             botReplyContainer.innerHTML = lastBotMessage.innerHTML;
             botReplyContainer.querySelectorAll('a').forEach(a => a.remove());
             const botReplyText = botReplyContainer.textContent.trim();

             if (confirm("Report the last bot response for human review?")) {
                socket.emit('report_message', {
                    user_msg: userMsg,
                    bot_reply: botReplyText
                });
             }
        } else {
            alert("The last two messages must be a User-Bot pair to report.");
        }
    }

    socket.on('report_confirmed', function(data) {
        alert(data.message);
    });


    // --- Other Event Listeners ---

    window.startListening = function() {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = "en-US";
        recognition.start();
        recognition.onresult = function (event) {
        const text = event.results[0][0].transcript;
        document.getElementById("userInput").value = text;
        window.send();
        };
    }

    document.getElementById("userInput").addEventListener("keypress", function (e) {
        if (e.key === "Enter") window.send();
    });