const countries = [
    { code: "+93", flag: "🇦🇫", name: "Afghanistan" },
    { code: "+355", flag: "🇦🇱", name: "Albania" },
    { code: "+213", flag: "🇩🇿", name: "Algeria" },
    { code: "+376", flag: "🇦🇩", name: "Andorra" },
    { code: "+244", flag: "🇦🇴", name: "Angola" },
    { code: "+54", flag: "🇦🇷", name: "Argentina" },
    { code: "+61", flag: "🇦🇺", name: "Australia" },
    { code: "+43", flag: "🇦🇹", name: "Austria" },
    { code: "+880", flag: "🇧🇩", name: "Bangladesh" },
    { code: "+32", flag: "🇧🇪", name: "Belgium" },
    { code: "+55", flag: "🇧🇷", name: "Brazil" },
    { code: "+1", flag: "🇨🇦", name: "Canada" },
    { code: "+86", flag: "🇨🇳", name: "China" },
    { code: "+33", flag: "🇫🇷", name: "France" },
    { code: "+49", flag: "🇩🇪", name: "Germany" },
    { code: "+91", flag: "🇮🇳", name: "India" },
    { code: "+62", flag: "🇮🇩", name: "Indonesia" },
    { code: "+39", flag: "🇮🇹", name: "Italy" },
    { code: "+81", flag: "🇯🇵", name: "Japan" },
    { code: "+254", flag: "🇰🇪", name: "Kenya" },
    { code: "+52", flag: "🇲🇽", name: "Mexico" },
    { code: "+234", flag: "🇳🇬", name: "Nigeria" },
    { code: "+92", flag: "🇵🇰", name: "Pakistan" },
    { code: "+7", flag: "🇷🇺", name: "Russia" },
    { code: "+27", flag: "🇿🇦", name: "South Africa" },
    { code: "+34", flag: "🇪🇸", name: "Spain" },
    { code: "+44", flag: "🇬🇧", name: "UK" },
    { code: "+1", flag: "🇺🇸", name: "USA" }
];

console.log("[v5] Registration script loaded");

const select = document.getElementById('countryCode');
if (select) {
    select.innerHTML = countries.map(c =>
        `<option value="${c.code}" ${c.code === "+91" ? 'selected' : ''}>
            ${c.flag} ${c.code}
        </option>`
    ).join('');
}

function togglePwd(inputId, icon) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = "password";
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

const form = document.getElementById('regForm');
const msg = document.getElementById('msg');

if (form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        console.log("[v5] Form submitted");

        const farmerID = document.getElementById('farmerID').value;
        const pass = document.getElementById('password').value;
        const confirmPass = document.getElementById('confirmPassword').value;
        const phoneSuf = document.getElementById('phone').value;
        const recovery_answer = document.getElementById('recoveryAnswer').value;

        if (!farmerID || !pass || !confirmPass || !phoneSuf || !recovery_answer) {
            showMsg("Please fill in all fields", "error");
            return;
        }

        if (pass !== confirmPass) {
            showMsg("Passwords do not match!", "error");
            return;
        }

        const btn = document.getElementById('registerBtn');
        btn.innerHTML = '<i class="fas fa-leaf fa-spin"></i> Registering...';

        const phone = (select ? select.value : "") + phoneSuf;
        const apiBaseUrl = 'http://localhost:8000/api';

        console.log("[v5] Sending register request to:", `${apiBaseUrl}/auth/register/`);

        fetch(`${apiBaseUrl}/auth/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: farmerID,
                phone: phone,
                recovery_answer: recovery_answer,
                password: pass
            }),
        })
            .then(async response => {
                const data = await response.json().catch(() => null);
                console.log("[v5] Response status:", response.status, data);
                if (!response.ok) {
                    throw new Error(data?.error || `Server returned ${response.status}`);
                }
                return data;
            })
            .then(data => {
                const msgText = data.message || "";
                console.log("[v5] Data received:", msgText);
                if (msgText.toLowerCase().includes("otp sent")) {
                    alert("OTP Sent! Check your phone.");
                    showMsg(msgText, "success");
                    const otpSection = document.getElementById('otpSection');
                    const registerBtn = document.getElementById('registerBtn');
                    if (otpSection) otpSection.style.display = 'block';
                    if (registerBtn) registerBtn.style.display = 'none';
                    if (otpSection) otpSection.scrollIntoView({ behavior: 'smooth' });
                } else {
                    showMsg("Registration successful! Redirecting...", "success");
                    setTimeout(() => {
                        window.location.href = "../Pages/login.html";
                    }, 2000);
                }
            })
            .catch((error) => {
                console.error('[v5 ERROR]', error);
                alert("v5 Critical Error: " + error.message);
                showMsg("Registration failed: " + error.message, "error");
            })
            .finally(() => {
                btn.innerHTML = 'Register Now <i class="fas fa-tractor"></i>';
            });
    });
}

const verifyOtpBtn = document.getElementById('verifyOtpBtn');
if (verifyOtpBtn) {
    verifyOtpBtn.addEventListener('click', function() {
        const farmerID = document.getElementById('farmerID').value;
        const otpCode = document.getElementById('regOtp').value;
        const apiBaseUrl = 'http://localhost:8000/api';
        
        if (!otpCode || otpCode.length !== 6) {
            showMsg("Please enter a valid 6-digit OTP", "error");
            return;
        }

        verifyOtpBtn.innerHTML = '<i class="fas fa-leaf fa-spin"></i> Verifying...';

        fetch(`${apiBaseUrl}/auth/verify-registration-otp/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                farmer_id: farmerID,
                otp_code: otpCode
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
            alert("OTP Verified! Registration Complete.");
            showMsg("Registration confirmed! Redirecting...", "success");
            setTimeout(() => {
                window.location.href = "../Pages/login.html";
            }, 2000);
        })
        .catch((error) => {
            alert("v5 Verification Error: " + error.message);
            showMsg("Verification failed: " + error.message, "error");
        })
        .finally(() => {
            verifyOtpBtn.innerHTML = 'Verify OTP <i class="fas fa-check-circle"></i>';
        });
    });
}

function showMsg(text, type) {
    if (msg) {
        msg.textContent = text;
        msg.className = type;
        msg.style.color = type === 'success' ? 'green' : 'red';
        msg.style.display = 'block';
    }
}
