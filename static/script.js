


const container = document.querySelector('.container');  
const registerBtn = document.querySelector('.register-btn');  
const loginBtn = document.querySelector('.login-btn');  

// Check that the buttons exist before attaching event listeners  
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