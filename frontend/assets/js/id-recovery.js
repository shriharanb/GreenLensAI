
async function verifyPhoneRecovery() {
    const phone = document.getElementById('phone').value.trim();
    const answer = document.getElementById('userAnswer').value.trim();

    if (!phone || !answer) {
        alert("Please fill in both fields");
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/api/auth/recover-id/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: phone,
                recovery_answer: answer
            })
        });

        const data = await response.json().catch(() => null);

        if (response.ok) {
            alert(`ID Recovered! Your Farmer ID is: ${data.farmer_id}`);
            window.location.href = 'login.html';
        } else {
            alert(data?.error || `Recovery failed (Server returned ${response.status})`);
        }
    } catch (err) {
        console.error('ID Recovery Error:', err);
        alert("Error: " + err.message);
    }
}