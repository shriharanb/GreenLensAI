
/* --- JAVASCRIPT LOGIC --- */

const form = document.getElementById('loginForm');
const messageDiv = document.getElementById('message');
const btn = document.querySelector('.login-btn');
const originalBtnText = btn?.innerHTML || 'Consult GreenLensAI';

const togglePassword = document.getElementById('togglePassword');
const passwordInput = document.getElementById('password');

if (togglePassword && passwordInput) {
    togglePassword.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });
}

if (form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (username === "" || password === "") {
            messageDiv.innerHTML = "Please fill in all fields.";
            messageDiv.className = "error";
            return;
        }

        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
        btn.style.opacity = "0.8";

        fetch('http://localhost:8000/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                farmer_id: username,
                password: password
            }),
        })
            .then(async response => {
                const data = await response.json().catch(() => null);
                if (!response.ok) {
                    throw new Error(data?.error || `Server returned ${response.status}`);
                }
                return data;
            })
            .then(data => {
                if (data.message && data.message.includes("successful")) {
                    localStorage.setItem("farmer_id", data.farmer_id);
                    messageDiv.innerHTML = "Login successful! Redirecting...";
                    messageDiv.className = "success";

                    if (data.farmer_id === 'admin') {
                        sessionStorage.setItem('adminAuth', 'true');
                        setTimeout(() => {
                            window.location.href = "admin.html";
                        }, 1000);
                    } else {
                        setTimeout(() => {
                            window.location.href = "../index.html";
                        }, 1000);
                    }
                } else {
                    messageDiv.innerHTML = data?.error || "Invalid credentials. Try again.";
                    messageDiv.className = "error";
                    btn.innerHTML = originalBtnText;
                    btn.style.opacity = "1";
                }
            })
            .catch((error) => {
                console.error('Login Error:', error);
                messageDiv.innerHTML = "Error: " + error.message;
                messageDiv.className = "error";
                btn.innerHTML = originalBtnText;
                btn.style.opacity = "1";
            });
    });
}
