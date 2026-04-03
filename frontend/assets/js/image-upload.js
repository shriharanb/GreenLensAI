let stream;

async function openCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" }
        });

        const video = document.getElementById("camera");
        video.srcObject = stream;
        video.hidden = false;

        document.getElementById("captureBtn").hidden = false;
    } catch (err) {
        alert("Camera access denied or not available");
        console.error(err);
    }
}

function capturePhoto() {
    const video = document.getElementById("camera");
    const canvas = document.getElementById("snapshot");
    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    // Convert to image
    const imageData = canvas.toDataURL("image/png");

    // Stop camera
    stream.getTracks().forEach(track => track.stop());
    video.hidden = true;
    document.getElementById("captureBtn").hidden = true;

    // Upload to backend
    fetch(imageData)
        .then(res => res.blob())
        .then(blob => {
            const file = new File([blob], "capture.png", { type: "image/png" });
            uploadImage(file);
        });
}

async function uploadImage(file) {
    const farmerId = localStorage.getItem("farmer_id") || "guest_farmer";
    const currentConversationId = localStorage.getItem("current_conversation_id");
    const formData = new FormData();
    formData.append("farmer_id", farmerId);
    formData.append("file", file);
    if (currentConversationId) {
        formData.append("conversation_id", currentConversationId);
    }

    // Get references for UI updates
    const messagesList = document.getElementById('messagesList');
    const chatContainer = document.getElementById('chatContainer');
    document.getElementById('welcomeScreen').style.display = 'none';

    // Show Analysis state
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot';
    loadingMsg.innerHTML = `<div class="avatar bot-av"><i class="fa-solid fa-leaf"></i></div><div class="message-content"><p><i class="fas fa-spinner fa-spin"></i> Analyzing image...</p></div>`;
    messagesList.appendChild(loadingMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        const response = await fetch("http://localhost:8000/api/image/predict/", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (loadingMsg.parentNode) messagesList.removeChild(loadingMsg);

        if (response.ok) {
            if (!currentConversationId && data.conversation_id) {
                currentConversationId = data.conversation_id;
                localStorage.setItem('current_conversation_id', currentConversationId);
                if (typeof loadChatHistory === 'function') loadChatHistory();
            }

            const userImgMsg = await createMessageElement("Uploaded an image for diagnosis", "user", data.image_url);
            messagesList.appendChild(userImgMsg);

            // Show the full LLM-generated response with disease name + solution
            const botText = data.bot_response || `Diagnosis: ${data.prediction} (Confidence: ${(data.confidence * 100).toFixed(2)}%)`;
            const botMsg = await createMessageElement(botText, "bot");
            messagesList.appendChild(botMsg);
        } else {
            const errorMsg = await createMessageElement(`Error: ${data.error || "Unknown error"}`, "bot");
            messagesList.appendChild(errorMsg);
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
        console.error("Upload error:", error);
        if (loadingMsg.parentNode) messagesList.removeChild(loadingMsg);
        alert("Failed to connect to backend for diagnosis.");
    }
}