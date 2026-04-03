// Simplified account recovery router
function selectOption(method) {
    document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
    document.getElementById(method + 'Option').classList.add('selected');
    window.currentMethod = method;
}

function proceed() {
    if (window.currentMethod === 'id') {
        window.location.href = 'id-recovery.html';
    } else if (window.currentMethod === 'password') {
        window.location.href = 'password-recovery.html';
    } else {
        alert('Please select an option to continue');
    }
}