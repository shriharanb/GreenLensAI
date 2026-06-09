GreenLensAI 1.0
GreenLensAI is an advanced, AI-powered agricultural assistant designed to empower farmers with real-time crop health monitoring, disease identification, and sustainable expert advice. By bridging the gap between cutting-edge AI and traditional farming, GreenLensAI helps ensure food security and optimized crop yields.

Key Features
Multilingual AI Chatbot: Conversational support in multiple languages (English, French, Spanish, Italian, Russian, and more) powered by the Qwen LLM.

Crop Disease Identification: Instant identification of plant diseases using computer vision and deep learning.

Expert Solutions (RAG): Retrieval-Augmented Generation using a Qdrant vector database to provide validated, expert-backed agricultural treatments.

Real-time Notifications: Automated daily SMS follow-ups via Twilio to guide farmers through multi-day treatment plans.

Integrated Vision: Support for direct camera capture and image uploads for immediate analysis.

Modern Web Interface: A sleek, responsive dashboard built with a focus on user experience and accessibility.

Tech Stack
Frontend
HTML5 & CSS3: Modern, responsive UI with custom animations.

Vanilla JavaScript: Lightweight and efficient client-side logic.

FontAwesome: Rich iconography for an intuitive interface.

Backend
Django & DRF: Robust API management and user authentication.

FastAPI: Specialized services for high-performance processing.

PostgreSQL: Reliable relational data storage.

AI and Machine Learning
Qwen2.5-0.5B-Instruct: Lightweight, high-performance LLM for conversational AI and translation.

Qdrant: Vector database for high-speed similarity search and RAG.

PyTorch & Transformers: Core frameworks for vision and language models.

OpenCV & Albumentations: Advanced image processing and augmentation.

Installation and Setup
Prerequisites
Python 3.10 or higher

PostgreSQL

CUDA-compatible GPU (Optional, for faster AI inference)

Steps
Clone the repository:

bash
git clone https://github.com/your-repo/GreenLensAI.git
cd GreenLensAI
Environment configuration:
Create a .env file in the root directory and add your credentials:

text
# Django Settings
SECRET_KEY=your_secret_key
DB_NAME=greenlens_db
DB_USER=your_user
DB_PASSWORD=your_password

# Twilio Credentials
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
Database setup:
Ensure PostgreSQL is running and create the database specified in your .env.

Run the initialization script:

bash
chmod +x start_server.sh
./start_server.sh
Project Structure
text
GreenLensAI/
├── backend/               # FastAPI microservices
├── backend_django/        # Main Django API application
│   ├── api/               # Core business logic (RAG, Vision, Agents)
│   └── greenlens/         # Project configuration
├── frontend/              # Web interface (HTML, CSS, JS)
├── data/                  # Knowledge base and vector data
├── models/                # Pre-trained ML models
├── scripts/               # Automation and utility scripts
└── start_server.sh        # All-in-one startup script
Usage
Once the start_server.sh script is running:

The backend will be live at http://localhost:8000.

The frontend will be served at http://localhost:3000.

Your default browser will automatically open the login page.

Contributing
We welcome contributions from the community. Whether it's improving AI models, adding new languages, or refining the UI, feel free to fork the repo and submit a PR.

License
This project is licensed under the MIT License - see the LICENSE file for details.

Built with love for the farming community.
