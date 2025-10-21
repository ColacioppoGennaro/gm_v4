<?php
/**
 * Database Migration Script - Google Calendar Fields
 * Visit this file in browser ONCE to run migration
 * Example: https://gruppogea.net/gm_v4/migrate_google_calendar.php
 * 
 * DELETE THIS FILE AFTER RUNNING!
 */

// Error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Prevent running twice
$lock_file = __DIR__ . '/.migration_google_calendar_done';
if (file_exists($lock_file)) {
    die('✅ Migration already completed! Delete this file: ' . basename(__FILE__));
}

// Load .env file manually
$env_file = __DIR__ . '/.env';
if (file_exists($env_file)) {
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue; // Skip comments
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value, " \t\n\r\0\x0B\"'"); // Remove quotes
        putenv("$name=$value");
        $_ENV[$name] = $value;
        $_SERVER[$name] = $value;
    }
}

// Database connection with error handling
$host = getenv('DB_HOST') ?: '127.0.0.1';
$dbname = getenv('DB_NAME') ?: 'ywrloefq_gm_v4';
$user = getenv('DB_USER') ?: 'ywrloefq_gm_user';
$pass = getenv('DB_PASS') ?: '';

// Debug info
echo "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Migration Status</title>";
echo "<style>body{font-family:Arial;max-width:800px;margin:50px auto;padding:20px;}";
echo "pre{background:#1F2937;color:#F3F4F6;padding:20px;border-radius:8px;overflow:auto;}";
echo ".error{color:#EF4444;}.success{color:#10B981;}</style></head><body>";

echo "<h1>🚀 Google Calendar Migration</h1>";
echo "<pre>";

echo "📋 Configuration:\n";
echo "   Host: $host\n";
echo "   Database: $dbname\n";
echo "   User: $user\n";
echo "   Password: " . (empty($pass) ? "EMPTY" : "***HIDDEN***") . "\n\n";

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    echo "✅ Database connection successful!\n\n";
    
    // Check current events table structure
    echo "📋 Checking current events table structure...\n";
    $stmt = $pdo->query("DESCRIBE events");
    $columns = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $has_google_event_id = in_array('google_event_id', $columns);
    $has_last_synced_at = in_array('last_synced_at', $columns);
    
    if ($has_google_event_id && $has_last_synced_at) {
        echo "✅ Events table already has Google Calendar columns!\n";
    } else {
        echo "➕ Adding Google Calendar columns to events table...\n";
        
        if (!$has_google_event_id) {
            $pdo->exec("ALTER TABLE events ADD COLUMN google_event_id VARCHAR(255) NULL UNIQUE COMMENT 'Google Calendar event ID'");
            echo "   ✅ Added google_event_id column\n";
        }
        
        if (!$has_last_synced_at) {
            $pdo->exec("ALTER TABLE events ADD COLUMN last_synced_at TIMESTAMP NULL");
            echo "   ✅ Added last_synced_at column\n";
        }
        
        // Add index if not exists
        try {
            $pdo->exec("CREATE INDEX idx_google_event_id ON events(google_event_id)");
            echo "   ✅ Created index on google_event_id\n";
        } catch (PDOException $e) {
            if (strpos($e->getMessage(), 'Duplicate key name') !== false) {
                echo "   ℹ️  Index idx_google_event_id already exists\n";
            } else {
                throw $e;
            }
        }
    }
    
    echo "\n";
    
    // Check users table
    echo "📋 Checking current users table structure...\n";
    $stmt = $pdo->query("DESCRIBE users");
    $userColumns = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    $has_google_calendar_connected = in_array('google_calendar_connected', $userColumns);
    $has_google_access_token = in_array('google_access_token', $userColumns);
    $has_google_refresh_token = in_array('google_refresh_token', $userColumns);
    $has_google_token_expires = in_array('google_token_expires', $userColumns);
    
    if ($has_google_calendar_connected && $has_google_access_token && $has_google_refresh_token && $has_google_token_expires) {
        echo "✅ Users table already has all Google Calendar columns!\n";
    } else {
        echo "➕ Adding Google Calendar columns to users table...\n";
        
        if (!$has_google_calendar_connected) {
            $pdo->exec("ALTER TABLE users ADD COLUMN google_calendar_connected BOOLEAN DEFAULT FALSE");
            echo "   ✅ Added google_calendar_connected column\n";
        }
        
        if (!$has_google_access_token) {
            $pdo->exec("ALTER TABLE users ADD COLUMN google_access_token TEXT NULL");
            echo "   ✅ Added google_access_token column\n";
        }
        
        if (!$has_google_refresh_token) {
            $pdo->exec("ALTER TABLE users ADD COLUMN google_refresh_token TEXT NULL");
            echo "   ✅ Added google_refresh_token column\n";
        }
        
        if (!$has_google_token_expires) {
            $pdo->exec("ALTER TABLE users ADD COLUMN google_token_expires TIMESTAMP NULL");
            echo "   ✅ Added google_token_expires column\n";
        }
    }
    
    echo "\n";
    
    // Verify changes
    echo "📊 Verification:\n";
    
    $stmt = $pdo->query("SELECT COUNT(*) as total_events FROM events");
    $totalEvents = $stmt->fetch(PDO::FETCH_ASSOC)['total_events'];
    
    $stmt = $pdo->query("SELECT COUNT(*) as synced_events FROM events WHERE google_event_id IS NOT NULL");
    $syncedEvents = $stmt->fetch(PDO::FETCH_ASSOC)['synced_events'];
    
    $stmt = $pdo->query("SELECT COUNT(*) as total_users FROM users");
    $totalUsers = $stmt->fetch(PDO::FETCH_ASSOC)['total_users'];
    
    $stmt = $pdo->query("SELECT COUNT(*) as connected_users FROM users WHERE google_calendar_connected = TRUE");
    $connectedUsers = $stmt->fetch(PDO::FETCH_ASSOC)['connected_users'];
    
    echo "   📅 Total events: $totalEvents\n";
    echo "   🔗 Synced with Google: $syncedEvents\n";
    echo "   👥 Total users: $totalUsers\n";
    echo "   🔗 Connected to Google Calendar: $connectedUsers\n";
    
    echo "\n";
    echo "✅ Migration completed successfully!\n";
    echo "🗑️  You can now DELETE this file: migrate_google_calendar.php\n";
    
    // Create lock file
    file_put_contents($lock_file, date('Y-m-d H:i:s'));
    
    echo "</pre>";
    
} catch (PDOException $e) {
    echo "</pre>";
    echo "<pre class='error'>";
    echo "❌ Database error:\n\n";
    echo "Error: " . $e->getMessage() . "\n";
    echo "Code: " . $e->getCode() . "\n\n";
    echo "Possible causes:\n";
    echo "1. Wrong database credentials in .env file\n";
    echo "2. Database server not accessible\n";
    echo "3. Database doesn't exist\n";
    echo "4. User doesn't have permissions\n\n";
    echo "Check your .env file at: " . $env_file . "\n";
    echo "</pre></body></html>";
    exit(1);
} catch (Exception $e) {
    echo "</pre>";
    echo "<pre class='error'>";
    echo "❌ Unexpected error:\n\n";
    echo $e->getMessage() . "\n";
    echo "</pre></body></html>";
    exit(1);
}

echo "</body></html>";
?>

```
