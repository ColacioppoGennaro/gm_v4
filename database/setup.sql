-- SmartLife Organizer v4 - Database Setup Script
-- Run this to initialize the database

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `ywrloefq_gm_v4` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- Use the database
USE `ywrloefq_gm_v4`;

-- Set SQL mode for better compatibility
SET SQL_MODE = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';

-- Enable event scheduler for cron-like functionality
SET GLOBAL event_scheduler = ON;

-- Source the main schema
-- In cPanel, you'll need to copy-paste the schema.sql content after this

-- Verify tables were created
SHOW TABLES;

-- Check default categories procedure
SHOW PROCEDURE STATUS WHERE Name = 'CreateDefaultCategories';