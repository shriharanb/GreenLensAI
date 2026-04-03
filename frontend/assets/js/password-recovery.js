
async function sendOTP() {
  const farmerId = document.getElementById("farmerId").value.trim();
  const messageDiv = document.getElementById("message");
  const sendBtn = document.getElementById("sendOtpBtn");

  if (!farmerId) {
    alert("Please enter your Farmer ID.");
    return;
  }

  sendBtn.disabled = true;
  sendBtn.innerHTML = '<span>Sending...</span> <i class="fas fa-spinner fa-spin"></i>';

  try {
    const response = await fetch('http://localhost:8000/api/auth/request-recovery-otp/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ farmer_id: farmerId })
    });

    const data = await response.json().catch(() => null);

    if (response.ok) {
      document.getElementById('otp-section').style.display = 'block';
      messageDiv.style.color = "green";
      messageDiv.textContent = data.message;
      sendBtn.innerHTML = '<span>Resend OTP</span> <i class="fa-solid fa-rotate"></i>';
    } else {
      messageDiv.style.color = "red";
      messageDiv.textContent = data?.error || "Failed to send OTP";
      sendBtn.innerHTML = '<span>Send OTP</span> <i class="fa-solid fa-paper-plane"></i>';
    }
  } catch (err) {
    console.error('OTP Request Error:', err);
    messageDiv.style.color = "red";
    messageDiv.textContent = "Error: " + err.message;
    sendBtn.innerHTML = '<span>Send OTP</span> <i class="fa-solid fa-paper-plane"></i>';
  } finally {
    sendBtn.disabled = false;
  }
}

async function verifyOTP() {
  const farmerId = document.getElementById("farmerId").value.trim();
  const otpCode = document.getElementById("otpCode").value.trim();
  const messageDiv = document.getElementById("message");

  if (!otpCode || otpCode.length !== 6) {
    alert("Please enter a valid 6-digit OTP.");
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/auth/verify-recovery-otp/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        farmer_id: farmerId,
        otp_code: otpCode
      })
    });

    const data = await response.json().catch(() => null);

    if (response.ok) {
      document.getElementById('step1').style.display = 'none';
      document.getElementById('step2').style.display = 'block';
      messageDiv.style.color = "green";
      messageDiv.textContent = data.message;
    } else {
      messageDiv.style.color = "red";
      messageDiv.textContent = data?.error || "OTP verification failed";
    }
  } catch (err) {
    console.error('OTP Verification Error:', err);
    messageDiv.style.color = "red";
    messageDiv.textContent = "Error: " + err.message;
  }
}

async function resetPassword() {
  const farmerId = document.getElementById("farmerId").value.trim();
  const otpCode = document.getElementById("otpCode").value.trim();
  const newPassword = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const messageDiv = document.getElementById("message");

  if (newPassword !== confirmPassword) {
    alert("Passwords do not match");
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/auth/reset-password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        farmer_id: farmerId,
        new_password: newPassword,
        otp_code: otpCode
      })
    });

    const data = await response.json().catch(() => null);

    if (response.ok) {
      messageDiv.style.color = "green";
      messageDiv.textContent = "Password reset successful! Redirecting to login...";
      setTimeout(() => {
        window.location.href = "login.html";
      }, 2000);
    } else {
      messageDiv.style.color = "red";
      messageDiv.textContent = data?.error || `Reset failed (Server returned ${response.status})`;
    }
  } catch (err) {
    console.error('Password Reset Error:', err);
    messageDiv.style.color = "red";
    messageDiv.textContent = "Error: " + err.message;
  }
}