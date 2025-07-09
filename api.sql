-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(255),
    balance DECIMAL(10,2) DEFAULT 0.00,
    orders INT DEFAULT 0,
    spent DECIMAL(10,2) DEFAULT 0.00
);

-- Create keys table
CREATE TABLE keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key VARCHAR(255) NOT NULL,
    game VARCHAR(50),
    duration VARCHAR(50),
    status ENUM('unused', 'used') DEFAULT 'unused',
    buyer_id BIGINT DEFAULT NULL,
    order_id VARCHAR(100) DEFAULT NULL,
    used_at TIMESTAMP NULL DEFAULT NULL
);

-- Create admin table
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Insert default admin
INSERT INTO admin (username, password) VALUES ('tola', 'tolalogin009@@');