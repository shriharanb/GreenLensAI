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

        const farmerID = document.getElementById('farmerID').value;
        const pass = document.getElementById('password').value;
        const confirmPass = document.getElementById('confirmPassword').value;

        const idPattern = /^(?!.*\.\.)[a-zA-Z_][\w.]{1,28}[a-zA-Z_]$/;

        if (!idPattern.test(farmerID)) {
            showMsg("ID must start/end with a letter or _, 3-30 chars, and no double dots.", "error");
            return;
        }

        const strongPwd = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
        if (!strongPwd.test(pass)) {
            showMsg("Password must be 8+ chars with Uppercase, Number, and Symbol.", "error");
            return;
        }

        if (pass !== confirmPass) {
            showMsg("Passwords do not match!", "error");
            return;
        }

        const btn = document.querySelector('.submit-btn');
        btn.innerHTML = '<i class="fas fa-leaf fa-spin"></i> Registering...';

        const phone = select.value + document.getElementById('phone').value;
        const recovery_answer = document.getElementById('recoveryAnswer').value;

        const apiBaseUrl = 'http://localhost:8000/api'; // Change to the actual backend IP if needed

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
                console.log("[DEBUG] Register initial response:", response.status, data);
                if (!response.ok) {
                    throw new Error(data?.error || `Server returned ${response.status}`);
                }
                return data;
            })
            .then(data => {
                const msgText = data.message || "";
                if (msgText.toLowerCase().includes("otp sent")) {
                    console.log("[DEBUG] OTP sent, switching UI to OTP section");
                    showMsg(msgText, "success");
                    document.getElementById('otpSection').style.display = 'block';
                    document.getElementById('registerBtn').style.display = 'none';
                    document.getElementById('otpSection').scrollIntoView({ behavior: 'smooth' });
                } else {
                    console.log("[DEBUG] Direct registration success (no OTP step triggered)");
                    showMsg("Registration successful! Redirecting to login...", "success");
                    setTimeout(() => {
                        window.location.href = "../Pages/login.html";
                    }, 2000);
                }
            })
            .catch((error) => {
                console.error('[CRITICAL] Registration Error:', error);
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

        console.log("[DEBUG] Verifying OTP for:", farmerID);
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
            console.log("[DEBUG] Verify OTP response:", response.status, data);
            if (!response.ok) {
                throw new Error(data?.error || `Server returned ${response.status}`);
            }
            return data;
        })
        .then(data => {
            console.log("[DEBUG] OTP Verification Success");
            showMsg("Registration confirmed! Redirecting to login...", "success");
            setTimeout(() => {
                window.location.href = "../Pages/login.html";
            }, 2000);
        })
        .catch((error) => {
            console.error('[CRITICAL] Verification Error:', error);
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
    }
}