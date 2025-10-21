-- Migration: Add missing Google Calendar fields if not exist
-- Run this on production database

-- Check current events table structure
DESCRIBE events;

-- Add columns if they don't exist (safe for existing tables)
ALTER TABLE events 
    ADD COLUMN IF NOT EXISTS google_event_id VARCHAR(255) NULL UNIQUE COMMENT 'Google Calendar event ID',
    ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP NULL;

-- Add index if not exists
CREATE INDEX IF NOT EXISTS idx_google_event_id ON events(google_event_id);

-- Check users table structure
DESCRIBE users;

-- Add Google Calendar columns to users if not exist
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_calendar_connected BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS google_access_token TEXT NULL,
    ADD COLUMN IF NOT EXISTS google_refresh_token TEXT NULL,
    ADD COLUMN IF NOT EXISTS google_token_expires TIMESTAMP NULL;

-- Verify changes
SELECT 
    'Events table updated' as status,
    COUNT(*) as total_events,
    SUM(CASE WHEN google_event_id IS NOT NULL THEN 1 ELSE 0 END) as synced_events
FROM events;

SELECT
    'Users table updated' as status,
    COUNT(*) as total_users,
    SUM(CASE WHEN google_calendar_connected = TRUE THEN 1 ELSE 0 END) as connected_users
FROM users;
