-- SmartLife Organizer v4 - MySQL Database Schema
-- Adapted for MariaDB/MySQL from PostgreSQL original design

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Set timezone
SET time_zone = '+00:00';

-- ================================
-- USERS TABLE
-- ================================
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token CHAR(36) NULL,
    password_reset_token CHAR(36) NULL,
    password_reset_expires TIMESTAMP NULL,
    subscription_type ENUM('free', 'pro') DEFAULT 'free',
    subscription_start_date TIMESTAMP NULL,
    subscription_end_date TIMESTAMP NULL,
    google_calendar_connected BOOLEAN DEFAULT FALSE,
    google_access_token TEXT NULL,
    google_refresh_token TEXT NULL,
    google_token_expires TIMESTAMP NULL,
    notification_preferences JSON DEFAULT ('{"push": true, "email": true}'),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    fcm_token VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_subscription_type (subscription_type),
    INDEX idx_email_verification_token (email_verification_token),
    INDEX idx_password_reset_token (password_reset_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- CATEGORIES TABLE
-- ================================
CREATE TABLE categories (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NOT NULL COMMENT 'Hex color: #RRGGBB',
    icon VARCHAR(50) NULL COMMENT 'Icon name or emoji',
    is_default BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_category (user_id, name),
    INDEX idx_user_display_order (user_id, display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- EVENTS TABLE
-- ================================
CREATE TABLE events (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    category_id CHAR(36) NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NULL,
    all_day BOOLEAN DEFAULT FALSE,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    amount DECIMAL(10,2) NULL COMMENT 'Amount if extracted from document',
    currency VARCHAR(3) DEFAULT 'EUR',
    google_event_id VARCHAR(255) NULL UNIQUE COMMENT 'Google Calendar event ID',
    last_synced_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_user_start_datetime (user_id, start_datetime),
    INDEX idx_user_status (user_id, status),
    INDEX idx_google_event_id (google_event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- DOCUMENTS TABLE
-- ================================
CREATE TABLE documents (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    event_id CHAR(36) NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL COMMENT 'Path on filesystem',
    file_type VARCHAR(50) NOT NULL COMMENT 'MIME type',
    file_size BIGINT NOT NULL COMMENT 'Size in bytes',
    extracted_text TEXT NULL COMMENT 'Text extracted via OCR/AI',
    ai_summary TEXT NULL COMMENT 'AI-generated summary',
    extracted_date DATE NULL COMMENT 'Due date extracted from document',
    extracted_amount DECIMAL(10,2) NULL,
    extracted_reason VARCHAR(255) NULL COMMENT 'Purpose/reason extracted',
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE COMMENT 'AI processing completed',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL,
    INDEX idx_user_upload_date (user_id, upload_date DESC),
    INDEX idx_event_id (event_id),
    INDEX idx_processed (processed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- REMINDERS TABLE
-- ================================
CREATE TABLE reminders (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    event_id CHAR(36) NOT NULL,
    reminder_datetime TIMESTAMP NOT NULL,
    notification_type ENUM('push', 'email', 'both') NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_reminder_datetime_sent (reminder_datetime, sent),
    INDEX idx_event_id (event_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- AI QUERIES LOG TABLE
-- ================================
CREATE TABLE ai_queries_log (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NULL,
    query_type ENUM('event_creation', 'document_analysis', 'general_query') NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    query_date DATE NOT NULL COMMENT 'Date only for daily counting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_query_date (user_id, query_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- DOCUMENT UPLOADS LOG TABLE
-- ================================
CREATE TABLE document_uploads_log (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    document_id CHAR(36) NOT NULL,
    upload_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_user_upload_date (user_id, upload_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- VECTOR EMBEDDINGS TABLE (JSON-based for MySQL)
-- ================================
CREATE TABLE vector_embeddings (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    document_id CHAR(36) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding JSON NOT NULL COMMENT 'Vector embedding as JSON array',
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document_chunk (document_id, chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- SUBSCRIPTIONS TABLE
-- ================================
CREATE TABLE subscriptions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL UNIQUE,
    plan_type ENUM('monthly', 'annual') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    status ENUM('active', 'cancelled', 'past_due', 'unpaid') NOT NULL,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_stripe_subscription_id (stripe_subscription_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- STRIPE WEBHOOKS LOG TABLE
-- ================================
CREATE TABLE stripe_webhooks_log (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSON NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_stripe_event_id (stripe_event_id),
    INDEX idx_processed_created (processed, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- ADMIN STATS TABLE
-- ================================
CREATE TABLE admin_stats (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    stat_date DATE NOT NULL UNIQUE,
    total_users INTEGER DEFAULT 0,
    free_users INTEGER DEFAULT 0,
    pro_users INTEGER DEFAULT 0,
    new_registrations INTEGER DEFAULT 0,
    new_subscriptions INTEGER DEFAULT 0,
    cancelled_subscriptions INTEGER DEFAULT 0,
    total_events_created INTEGER DEFAULT 0,
    total_documents_uploaded INTEGER DEFAULT 0,
    total_ai_queries INTEGER DEFAULT 0,
    revenue_daily DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_stat_date_desc (stat_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================
-- DEFAULT CATEGORIES INSERT PROCEDURE
-- ================================
DELIMITER //

CREATE PROCEDURE CreateDefaultCategories(IN p_user_id CHAR(36))
BEGIN
    INSERT INTO categories (user_id, name, color, icon, is_default, display_order) VALUES
    (p_user_id, 'Lavoro', '#3B82F6', '💼', TRUE, 1),
    (p_user_id, 'Famiglia', '#10B981', '👨‍👩‍👧', TRUE, 2),
    (p_user_id, 'Personale', '#8B5CF6', '🧘', TRUE, 3),
    (p_user_id, 'Altro', '#6B7280', '📌', TRUE, 4);
END//

DELIMITER ;

-- ================================
-- TRIGGERS FOR UPDATED_AT
-- ================================
-- Users table trigger
DELIMITER //
CREATE TRIGGER tr_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
BEGIN 
    SET NEW.updated_at = CURRENT_TIMESTAMP; 
END//
DELIMITER ;

-- Categories table trigger
DELIMITER //
CREATE TRIGGER tr_categories_updated_at 
    BEFORE UPDATE ON categories 
    FOR EACH ROW 
BEGIN 
    SET NEW.updated_at = CURRENT_TIMESTAMP; 
END//
DELIMITER ;

-- Events table trigger
DELIMITER //
CREATE TRIGGER tr_events_updated_at 
    BEFORE UPDATE ON events 
    FOR EACH ROW 
BEGIN 
    SET NEW.updated_at = CURRENT_TIMESTAMP; 
END//
DELIMITER ;

-- Subscriptions table trigger
DELIMITER //
CREATE TRIGGER tr_subscriptions_updated_at 
    BEFORE UPDATE ON subscriptions 
    FOR EACH ROW 
BEGIN 
    SET NEW.updated_at = CURRENT_TIMESTAMP; 
END//
DELIMITER ;

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

-- Composite indexes for common queries
CREATE INDEX idx_events_user_datetime_status ON events(user_id, start_datetime, status);
CREATE INDEX idx_reminders_pending ON reminders(reminder_datetime, sent) WHERE sent = FALSE;
CREATE INDEX idx_documents_user_processed ON documents(user_id, processed, upload_date);

-- Full-text search indexes
ALTER TABLE events ADD FULLTEXT(title, description);
ALTER TABLE documents ADD FULLTEXT(extracted_text, ai_summary);

-- ================================
-- VIEWS FOR COMMON QUERIES
-- ================================

-- User dashboard events view
CREATE VIEW v_user_events AS
SELECT 
    e.id,
    e.user_id,
    e.title,
    e.description,
    e.start_datetime,
    e.end_datetime,
    e.all_day,
    e.status,
    e.amount,
    e.currency,
    c.name as category_name,
    c.color as category_color,
    c.icon as category_icon,
    EXISTS(SELECT 1 FROM documents d WHERE d.event_id = e.id) as has_document,
    EXISTS(SELECT 1 FROM reminders r WHERE r.event_id = e.id AND r.sent = FALSE) as has_active_reminder,
    e.google_event_id IS NOT NULL as synced_with_google
FROM events e
LEFT JOIN categories c ON e.category_id = c.id;

-- User subscription status view
CREATE VIEW v_user_subscription_status AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_type,
    u.subscription_end_date,
    s.status as stripe_status,
    s.cancel_at_period_end,
    s.current_period_end,
    CASE 
        WHEN u.subscription_type = 'pro' AND u.subscription_end_date > NOW() THEN TRUE
        ELSE FALSE
    END as is_pro_active
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active';

-- ================================
-- DATA CLEANUP PROCEDURES
-- ================================

-- Clean old logs procedure
DELIMITER //
CREATE PROCEDURE CleanOldLogs()
BEGIN
    -- Delete AI query logs older than 90 days
    DELETE FROM ai_queries_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
    
    -- Delete upload logs older than 90 days  
    DELETE FROM document_uploads_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
    
    -- Delete processed webhook logs older than 30 days
    DELETE FROM stripe_webhooks_log WHERE processed = TRUE AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Delete old email verification tokens
    UPDATE users SET email_verification_token = NULL 
    WHERE email_verification_token IS NOT NULL 
    AND created_at < DATE_SUB(NOW(), INTERVAL 1 DAY);
    
    -- Delete old password reset tokens
    UPDATE users SET password_reset_token = NULL, password_reset_expires = NULL
    WHERE password_reset_expires < NOW();
END//
DELIMITER ;

-- ================================
-- SAMPLE DATA FOR TESTING (OPTIONAL)
-- ================================

-- Insert test user (commented out for production)
-- INSERT INTO users (id, email, password_hash, email_verified) VALUES
-- (UUID(), 'test@smartlife.com', '$2b$12$hash_here', TRUE);

COMMIT;