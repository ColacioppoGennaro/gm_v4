import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # App settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'gm_v4_fallback_secret')
    APP_URI = os.getenv('APP_URI', 'https://gruppogea.net/gm_v4')
    ENV = os.getenv('APP_ENV', 'production')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_NAME = os.getenv('DB_NAME', 'ywrloefq_gm_v4')
    DB_USER = os.getenv('DB_USER', 'ywrloefq_gm_user')
    DB_PASS = os.getenv('DB_PASS', '')
    
    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_fallback_secret')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DELTA = 7 * 24 * 60 * 60  # 7 days in seconds
    
    # AI Services
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    DOCANALYZER_API_KEY = os.getenv('DOCANALYZER_API_KEY', '')
    
    # Google Calendar OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', '')
    GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    
    # Push notifications
    PWA_PUSH = os.getenv('PWA_PUSH', 'true').lower() == 'true'
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
    PUSH_SUBJECT = os.getenv('PUSH_SUBJECT', 'mailto:admin@gruppogea.net')
    
    # Email configuration
    MAIL_ENABLED = os.getenv('MAIL_ENABLED', 'false').lower() == 'true'
    MAIL_HOST = os.getenv('MAIL_HOST', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_FROM = os.getenv('MAIL_FROM', 'notifiche@gruppogea.net')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'SmartLife Organizer')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PRICE_ID_MONTHLY = os.getenv('STRIPE_PRICE_ID_MONTHLY', '')
    STRIPE_PRICE_ID_ANNUAL = os.getenv('STRIPE_PRICE_ID_ANNUAL', '')
    
    # File upload settings
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    FREE_PLAN_AI_QUERIES_DAILY = int(os.getenv('FREE_PLAN_AI_QUERIES_DAILY', 20))
    FREE_PLAN_DOCUMENTS_DAILY = int(os.getenv('FREE_PLAN_DOCUMENTS_DAILY', 20))
    
    @staticmethod
    def get_db_connection_string():
        """Get MySQL connection string"""
        return f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}/{Config.DB_NAME}?charset=utf8mb4"
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS