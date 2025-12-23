import { initializeApp } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-auth.js";
import { getFirestore, doc, setDoc } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-firestore.js";
import { firebaseConfig, emailConfig } from '../config.js';
import { emailConfig } from '../config.js';

emailjs.init(emailConfig.PUBLIC_KEY);

    // 2. Initialize the App
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getFirestore(app);
    // Export them for use in other files
    export { auth, db };
// PASSWORD TOGGLE FUNCTION
  window.togglePassword = function() {
  const passwordInput = document.getElementById("password");
  const toggleIcon = document.getElementById("toggleIcon");

  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    // Ensure this path is correct if not using a CDN for the icon
    toggleIcon.src = "../static/visibility_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png"; 
  } else {
    passwordInput.type = "password";
    // Ensure this path is correct if not using a CDN for the icon
    toggleIcon.src = "../static/visibility_off_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.png";
  }
}
    window.togglePassword = togglePassword;
    // Attach togglePassword to the window object or call it directly via the onclick in HTML
    // window.togglePassword = togglePassword; 


    document.getElementById("form").addEventListener("submit", function (e) {
      const termsChecked = document.getElementById("terms").checked;
      // Prevent default submission if terms are not checked
      if (!termsChecked) {
        e.preventDefault(); 
        showMessage("You must agree to the Terms and Conditions.", "signUpMessage");
      } 
    });
// 3. MESSAGE FUNCTION
function showMessage(message, divId) {
    const messageDiv = document.getElementById(divId);
    messageDiv.style.display = "block";
    messageDiv.innerHTML = message;
    messageDiv.style.background = "#d9534f"; // Set a background for error/message
    messageDiv.style.color = "white"; // Ensure text is visible
    messageDiv.style.opacity = 1;

    setTimeout(() => {
        messageDiv.style.opacity = 0;
        messageDiv.style.display = "none";
    }, 5000);
}
const signUp = document.getElementById('submit'); 

signUp.addEventListener('click', async (event) => {
    event.preventDefault(); 

    const termsChecked = document.getElementById("terms").checked;
    if (!termsChecked) {
        showMessage("You must agree to the Terms and Conditions.", "signUpMessage");
        return;
    }

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const firstName = document.getElementById('firstname').value.trim(); 
    const lastName = document.getElementById('lastname').value.trim(); 
    const username = firstName + lastName; // Creating a username for SQLite

    const submitBtn = document.getElementById('submit');
    submitBtn.disabled = true;
    submitBtn.innerText = "Processing...";

    try {
        // 1. Create user in Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        // 2. Save user data to Firestore
        const docRef = doc(db, "users", user.uid);
        await setDoc(docRef, {
            email: email,
            firstName: firstName,
            lastName: lastName,
            createdAt: new Date()
        });
        const flaskResponse = await fetch('/register.html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
        });

const flaskData = await flaskResponse.json();
        if (flaskData.status !== "success") {
            throw new Error("Local Database sync failed: " + flaskData.message);
        }

        // STEP 4: Send Welcome Email via EmailJS
        const templateParams = {
            firstName: firstName,
            email: email,
            reply_to: 'support@yourwebsite.com'
        };

        await window.emailjs.send(emailConfig.SERVICE_ID, emailConfig.TEMPLATE_ID_REGISTER, templateParams)

        // STEP 5: Success & Redirect
        showMessage("Registration Successful! Redirecting...", "signUpMessage", false);
        setTimeout(() => { window.location.href = 'login.html'; }, 2000);

    } catch (error) {
        console.error("Sign Up Error:", error);
        submitBtn.disabled = false;
        submitBtn.innerText = "Sign Up";

        let msg = "An error occurred during registration.";
        if (error.code === 'auth/email-already-in-use') msg = 'Email already exists!';
        if (error.code === 'auth/weak-password') msg = 'Password is too weak.';
        
        showMessage(error.message || msg, "signUpMessage");
    }
});