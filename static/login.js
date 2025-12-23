    console.log("Full Env Object:", import.meta.env);
    // 1. IMPORT FIREBASE MODULES
    import { initializeApp } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-app.js";
    import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-auth.js";
    import { firebaseConfig } from './config.js';

// Now use firebaseConfig.apiKey etc.
    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);

    export { app, auth };
    
    
    // 3. MESSAGE FUNCTION
    // This function handles showing temporary messages to the user.
    // It assumes your login page has an element with the ID that is passed as divId
    function showMessage(message, divId) {
     const messageDiv = document.getElementById(divId);
     // Ensure the div exists before trying to modify it
     if (!messageDiv) return;
    
     messageDiv.style.display = "block";
     messageDiv.innerHTML = message;
     
     // Use a different color for success or just keep error styling for failed attempts
     if (message.includes("Success")) {
    messageDiv.style.background = "#5cb85c"; // Green for success
     } else {
    messageDiv.style.background = "#d9534f"; // Red for error
     }
     
     messageDiv.style.color = "white";
     messageDiv.style.opacity = 1;
    
     setTimeout(() => {
     // Add a slight transition for the fade-out effect (assuming you have one in your CSS or rely on default)
     messageDiv.style.opacity = 0; 
     
     // Wait for the transition to finish before setting display: none
     setTimeout(() => {
    messageDiv.style.display = "none";
    // Reset background color for next message (optional)
    messageDiv.style.background = "transparent";
     }, 500); // 500ms transition fade time
    
     }, 5000);
    }
    
    // Function to toggle password visibility (for convenience, assuming similar HTML)
    function togglePassword() {
     const passwordInput = document.getElementById("password");
     const toggleIcon = document.getElementById("toggleIcon");
     
     if (passwordInput.type === "password") {
    passwordInput.type = "text";
    // Update to your correct icon paths - assuming visibility_24dp is the open eye
    toggleIcon.src = "../static/images/visibility_off_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png"; 
     } else {
    passwordInput.type = "password";
    // Update to your correct icon paths - assuming visibility_off_24dp is the closed eye
    toggleIcon.src = "../static/images/visibility_off_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png";
     }
    }
    window.togglePassword = togglePassword; // Expose to global scope for HTML onclick
    
    // 4. LOGIN EVENT LISTENER
    const loginButton = document.getElementById('submit'); // Assuming the login button ID is 'submit'
    // *** FIX: Changed to match the HTML div ID 'signUpMessage' ***
    const messageDivId = 'signUpMessage'; 
    
loginButton.addEventListener('click', async (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !password) {
        showMessage("Please enter both email and password.", messageDivId);
        return;
    }

    try {
        // Step 1: Client-side Firebase Check
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        console.log("Firebase Auth Success");

        // Step 2: Server-side Flask Session Bridge
        // ... inside your fetch(...).then block
const response = await fetch('/login', { // Ensure no trailing slash here
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
});

const data = await response.json(); // Read the JSON from Flask

if (data.status === "success") {
    showMessage("Login Successful! Redirecting...", messageDivId);
    setTimeout(() => {
        window.location.href = data.redirect; // This moves the browser to /chat
    }, 1000);
} else {
    showMessage(data.message || "Login failed", messageDivId);
}

    } catch (error) {
        console.error("Login Error:", error);
        showMessage("Invalid credentials or connection error.", messageDivId);
    }
});