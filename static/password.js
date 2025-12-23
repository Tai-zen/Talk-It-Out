    import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
    import { getAuth, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
    import { getFirestore } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
    import { firebaseConfig, emailConfig } from '../config.js';
    import { emailConfig } from '../config.js';
    // 2. Initialize the App
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getFirestore(app);
    // Export them for use in other files
    export { auth, db };

    const messageDiv = document.getElementById('resetMessage');

    function showMessage(message, isSuccess = true) {
      messageDiv.textContent = message;
      messageDiv.classList.remove('hidden', 'error', 'success');
      messageDiv.classList.add(isSuccess ? 'success' : 'error');
      setTimeout(() => messageDiv.classList.add('hidden'), 5000);
    }

    document.getElementById('resetForm').addEventListener('submit', async (event) => {
      event.preventDefault();
      const emailInput = document.getElementById('email');
      const email = emailInput.value.trim();
      if (!email) {
        showMessage("Please enter your email address.", false);
        return;
      }

      const button = document.getElementById('resetPasswordBtn');
      const originalText = button.textContent;
      button.disabled = true;
      button.textContent = "Sending...";

      try {
        await sendPasswordResetEmail(auth, email);
        showMessage(`Password reset link sent to ${email}. Check your inbox.`, true);
        emailInput.value = '';
      } catch (error) {
        let errorMessage = "An error occurred. Please try again.";
        if (error.code === 'auth/user-not-found') errorMessage = "No user found with that email address.";
        else if (error.code === 'auth/invalid-email') errorMessage = "The email address format is invalid.";
        else if (error.code === 'auth/missing-email') errorMessage = "Email address is required.";
        showMessage(errorMessage, false);
      } finally {
        button.disabled = false;
        button.textContent = originalText;
      }
    });