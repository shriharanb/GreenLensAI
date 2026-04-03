-- Create the database
-- CREATE DATABASE greenlensai;

-- Farmers (Users) Table
CREATE TABLE IF NOT EXISTS farmers (
    farmer_id VARCHAR(50) PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    recovery_answer VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat History Table
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    farmer_id VARCHAR(50) REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    message_type VARCHAR(10) CHECK (message_type IN ('user', 'bot')),
    content TEXT,
    image_path TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
