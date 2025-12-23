import { initializeApp } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-app.js";
        import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-auth.js";
        import { getFirestore, doc, onSnapshot, updateDoc } from "https://www.gstatic.com/firebasejs/10.6.0/firebase-firestore.js";
        import { firebaseConfig } from './config.js';
        import { getFirestore } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
    import { firebaseConfig, emailConfig } from './config.js';
    import { emailConfig } from './config.js';
    import { interswitchConfig } from './config.js';
    // 2. Initialize the App
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const db = getFirestore(app);
    // Export them for use in other files
    export { auth, db };
    
        let currentUser = null;
    
        onAuthStateChanged(auth, (user) => {
            if (user) {
                currentUser = user;
                checkSubscription(user.uid);
            } else {
                // If user is not logged in, redirect to login page
                // Adjust this path if your login file is in a different folder
                window.location.href = "login.html"; 
            }
        });
    
        function checkSubscription(uid) {
            const userDocRef = doc(db, "users", uid);
            
            onSnapshot(userDocRef, (docSnap) => {
                const loadingEl = document.getElementById('loading-state');
                if (loadingEl) loadingEl.style.display = 'none';
                
                const data = docSnap.data();
                const lockedEl = document.getElementById('locked-state');
                const premiumEl = document.getElementById('premium-content');
                const expiryNotice = document.getElementById('expiry-notice');
    
                const now = new Date();
                const expiryDate = data?.expiryDate ? new Date(data.expiryDate) : null;
    
                // VALIDATION: Is status active AND is the date still valid?
                if (data?.subscriptionStatus === 'active' && expiryDate && expiryDate > now) {
                    lockedEl.style.display = 'none';
                    premiumEl.style.display = 'block';
                    
                    const daysLeft = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
                    expiryNotice.innerText = `Your subscription expires in ${daysLeft} days.`;
                } else {
                    lockedEl.style.display = 'block';
                    premiumEl.style.display = 'none';
                    initPayButton();
                }
            });
        }
    
        function initPayButton() {
            const payBtn = document.getElementById("payBtn");
            if (!payBtn) return;

            // Clone to remove old listeners
            const newBtn = payBtn.cloneNode(true);
            payBtn.parentNode.replaceChild(newBtn, payBtn);
            newBtn.addEventListener("click", () => {
            const paymentRequest = {
                // Use environment variables here
                merchant_code: interswitchConfig.MERCHANT_CODE,
                pay_item_id: interswitchConfig.PAY_ITEM_ID,
                mode: interswitchConfig.MODE,
                site_redirect_url: interswitchConfig.REDIRECT_URL,
                onComplete: (res) => {
                    if (res && (res.resp === "00" || res.status === "SUCCESS" || res.resp === "058")) {
                        processSuccessfulPayment();
                    } else {
                        // Optional: Handle failure/cancellation
                        alert("Payment failed or cancelled. Please try again.");
                        console.log("Payment response:", res);
                    }
                },
            };
                if (window.webpayCheckout) window.webpayCheckout(paymentRequest);
            });
        }
    
        // Add sendEmail call inside your existing function
async function processSuccessfulPayment() {
    if (!currentUser) return;

    const expiry = new Date();
    expiry.setDate(expiry.getDate() + 30);
    const expiryString = expiry.toLocaleDateString(); // Human-readable date for the email

    const userDocRef = doc(db, "users", currentUser.uid);
    
    try {
        // 1. Update Firestore first
        await updateDoc(userDocRef, { 
            subscriptionStatus: 'active',
            expiryDate: expiry.toISOString(),
            lastPaymentDate: new Date().toISOString()
        });

        // 2. Trigger EmailJS
        const templateParams = {
            email: currentUser.email,
            firstName: currentUser.displayName || "Subscriber",
            expiry_date: expiryString,
            message: "Your 30-day premium access to Sound Lounge is now active!"
        };

        await window.emailjs.send(emailConfig.SERVICE_ID, emailConfig.TEMPLATE_ID_PAYMENT, templateParams)
            .then((response) => {
               console.log('Email sent successfully!', response.status, response.text);
            }, (err) => {
               console.error('Email failed to send...', err);
            });

    } catch (e) {
        console.error("Error:", e);
        alert("Payment successful, but we had trouble updating your account.");
    }
}