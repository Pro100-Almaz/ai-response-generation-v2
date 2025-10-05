-- MySQL initialization script for ai-response-generation-v2
-- This script is executed when the MySQL container is first created

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `fastapi_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user if it doesn't exist and grant privileges
CREATE USER IF NOT EXISTS 'fastapi_user'@'%' IDENTIFIED BY 'fastapi_strong_pwd';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON `fastapi_db`.* TO 'fastapi_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Switch to the created database
USE `fastapi_db`;

-- Create initial tables (if needed)
-- This is where you can add any initial table creation
-- Note: Alembic migrations will handle the actual schema creation

-- Show current database and user
SELECT DATABASE() as current_database;
SELECT CURRENT_USER() as current_user;
