"""
Authentication utilities for SmartLife Organizer
"""

import jwt
import bcrypt
import secrets
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from config import Config
from modules.utils.database import db, generate_uuid

class AuthManager:
    """Handles authentication operations"""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_jwt_token(user_data):
        """Generate JWT token for user"""
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'subscription_type': user_data.get('subscription_type', 'free'),
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION_DELTA)
        }
        
        return jwt.encode(
            payload,
            Config.JWT_SECRET_KEY,
            algorithm=Config.JWT_ALGORITHM
        )
    
    @staticmethod
    def decode_jwt_token(token):
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET_KEY,
                algorithms=[Config.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    @staticmethod
    def generate_verification_token():
        """Generate email verification token"""
        return generate_uuid()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        return True, "Password is valid"
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email address"""
        query = """
            SELECT id, email, password_hash, email_verified, subscription_type,
                   onboarding_completed, google_calendar_connected, 
                   notification_preferences, created_at
            FROM users 
            WHERE email = %s
        """
        return db.execute_query(query, (email,), fetch_one=True)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        query = """
            SELECT id, email, password_hash, email_verified, subscription_type,
                   onboarding_completed, google_calendar_connected,
                   notification_preferences, created_at,
                   subscription_start_date, subscription_end_date
            FROM users 
            WHERE id = %s
        """
        return db.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def create_user(email, password, verification_token=None):
        """Create a new user"""
        password_hash = AuthManager.hash_password(password)
        user_id = generate_uuid()
        
        if not verification_token:
            verification_token = AuthManager.generate_verification_token()
        
        query = """
            INSERT INTO users (id, email, password_hash, email_verification_token)
            VALUES (%s, %s, %s, %s)
        """
        
        try:
            db.execute_query(query, (user_id, email, password_hash, verification_token), fetch_all=False)
            
            # Create default categories for user
            db.execute_query("CALL CreateDefaultCategories(%s)", (user_id,), fetch_all=False)
            
            return {
                'id': user_id,
                'email': email,
                'verification_token': verification_token
            }
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def verify_email(token):
        """Verify user email with token"""
        # Check if token exists and is not expired (24 hours)
        query = """
            UPDATE users 
            SET email_verified = TRUE, email_verification_token = NULL 
            WHERE email_verification_token = %s 
            AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
        """
        
        result = db.execute_query(query, (token,), fetch_all=False)
        return result > 0  # True if any row was updated
    
    @staticmethod
    def request_password_reset(email):
        """Request password reset for email"""
        user = AuthManager.get_user_by_email(email)
        if not user:
            return None  # Don't reveal if email exists
        
        reset_token = generate_uuid()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        query = """
            UPDATE users 
            SET password_reset_token = %s, password_reset_expires = %s 
            WHERE email = %s
        """
        
        db.execute_query(query, (reset_token, expires_at, email), fetch_all=False)
        return reset_token
    
    @staticmethod
    def reset_password(token, new_password):
        """Reset password with token"""
        query = """
            UPDATE users 
            SET password_hash = %s, password_reset_token = NULL, password_reset_expires = NULL
            WHERE password_reset_token = %s 
            AND password_reset_expires > NOW()
        """
        
        password_hash = AuthManager.hash_password(new_password)
        result = db.execute_query(query, (password_hash, token), fetch_all=False)
        return result > 0

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication token required', 'success': False}), 401
        
        try:
            payload = AuthManager.decode_jwt_token(token)
            current_user = AuthManager.get_user_by_id(payload['user_id'])
            
            if not current_user:
                return jsonify({'error': 'Invalid token', 'success': False}), 401
            
            # Add current user to request context
            request.current_user = current_user
            
        except ValueError as e:
            return jsonify({'error': str(e), 'success': False}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication failed', 'success': False}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_pro_subscription(f):
    """Decorator to require Pro subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required', 'success': False}), 401
        
        user = request.current_user
        
        # Check if user has active Pro subscription
        if user['subscription_type'] != 'pro':
            return jsonify({
                'error': 'Pro subscription required',
                'success': False,
                'upgrade_required': True
            }), 403
        
        # Check if subscription is not expired
        if user.get('subscription_end_date') and user['subscription_end_date'] < datetime.utcnow():
            return jsonify({
                'error': 'Pro subscription has expired',
                'success': False,
                'upgrade_required': True
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def check_rate_limit(user_id, limit_type='ai_queries'):
    """Check if user has exceeded rate limits"""
    if limit_type == 'ai_queries':
        query = """
            SELECT COUNT(*) as count 
            FROM ai_queries_log 
            WHERE user_id = %s AND query_date = CURDATE()
        """
        result = db.execute_query(query, (user_id,), fetch_one=True)
        current_count = result['count'] if result else 0
        
        # Get user subscription type
        user = AuthManager.get_user_by_id(user_id)
        if user and user['subscription_type'] == 'pro':
            return True, current_count, -1  # Unlimited for Pro users
        
        limit = Config.FREE_PLAN_AI_QUERIES_DAILY
        return current_count < limit, current_count, limit
    
    elif limit_type == 'document_uploads':
        query = """
            SELECT COUNT(*) as count 
            FROM document_uploads_log 
            WHERE user_id = %s AND upload_date = CURDATE()
        """
        result = db.execute_query(query, (user_id,), fetch_one=True)
        current_count = result['count'] if result else 0
        
        # Get user subscription type
        user = AuthManager.get_user_by_id(user_id)
        if user and user['subscription_type'] == 'pro':
            return True, current_count, -1  # Unlimited for Pro users
        
        limit = Config.FREE_PLAN_DOCUMENTS_DAILY
        return current_count < limit, current_count, limit
    
    return True, 0, -1