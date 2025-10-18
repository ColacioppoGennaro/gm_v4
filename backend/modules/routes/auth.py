"""
Authentication routes for SmartLife Organizer
"""

from flask import Blueprint, request, jsonify
from modules.utils.auth import AuthManager, require_auth
from modules.utils.database import create_response, validate_required_fields
from modules.services.email_service import EmailService
import logging

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Configure logging
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['email', 'password', 'password_confirm'])
        
        email = data['email'].lower().strip()
        password = data['password']
        password_confirm = data['password_confirm']
        
        # Validate email format
        if not AuthManager.validate_email(email):
            return jsonify(create_response(
                error="Invalid email format",
                status_code=400
            ))
        
        # Validate password
        is_valid, message = AuthManager.validate_password(password)
        if not is_valid:
            return jsonify(create_response(
                error=message,
                status_code=400
            )), 400
        
        # Check password confirmation
        if password != password_confirm:
            return jsonify(create_response(
                error="Passwords do not match",
                status_code=400
            )), 400
        
        # Check if email already exists
        existing_user = AuthManager.get_user_by_email(email)
        if existing_user:
            return jsonify(create_response(
                error="Email already registered",
                status_code=409
            )), 409
        
        # Create user
        user_data = AuthManager.create_user(email, password)
        
        # Send verification email
        try:
            EmailService.send_verification_email(
                email, 
                user_data['verification_token']
            )
        except Exception as e:
            logger.warning(f"Failed to send verification email: {str(e)}")
            # Don't fail registration if email fails
        
        return jsonify(create_response(
            message="Registration successful. Please check your email to verify your account.",
            status_code=201
        )), 201
        
    except ValueError as e:
        return jsonify(create_response(
            error=str(e),
            status_code=400
        )), 400
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify(create_response(
            error="Registration failed. Please try again.",
            status_code=500
        )), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['email', 'password'])
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Get user by email
        user = AuthManager.get_user_by_email(email)
        if not user:
            return jsonify(create_response(
                error="Invalid credentials",
                status_code=401
            )), 401
        
        # TEMPORANEO: Skip email verification check per sviluppo
        # if not user['email_verified']:
        #     return jsonify(create_response(
        #         error="Email not verified. Please check your email and verify your account.",
        #         status_code=403
        #     )), 403
        
        # Verify password
        if not AuthManager.verify_password(password, user['password_hash']):
            return jsonify(create_response(
                error="Invalid credentials",
                status_code=401
            ))
        
        # Generate JWT token
        token = AuthManager.generate_jwt_token(user)
        
        # Prepare user data for response (exclude sensitive info)
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'subscription_type': user['subscription_type'],
            'onboarding_completed': user['onboarding_completed'],
            'google_calendar_connected': user['google_calendar_connected']
        }
        
        return jsonify(create_response(
            data={
                'token': token,
                'user': user_data
            },
            message="Login successful"
        ))
        
    except ValueError as e:
        return jsonify(create_response(
            error=str(e),
            status_code=400
        ))
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify(create_response(
            error="Login failed. Please try again.",
            status_code=500
        ))

@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    """Verify user email with token"""
    try:
        token = request.args.get('token')
        
        if not token:
            return jsonify(create_response(
                error="Verification token required",
                status_code=400
            ))
        
        # Verify email
        success = AuthManager.verify_email(token)
        
        if success:
            return jsonify(create_response(
                message="Email verified successfully. You can now log in.",
                status_code=200
            ))
        else:
            return jsonify(create_response(
                error="Invalid or expired verification token",
                status_code=400
            ))
        
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        return jsonify(create_response(
            error="Email verification failed",
            status_code=500
        ))

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['email'])
        
        email = data['email'].lower().strip()
        
        # Validate email format
        if not AuthManager.validate_email(email):
            return jsonify(create_response(
                error="Invalid email format",
                status_code=400
            ))
        
        # Request password reset (always return success for security)
        reset_token = AuthManager.request_password_reset(email)
        
        # Send reset email if user exists
        if reset_token:
            try:
                EmailService.send_password_reset_email(email, reset_token)
            except Exception as e:
                logger.warning(f"Failed to send password reset email: {str(e)}")
        
        # Always return success to prevent email enumeration
        return jsonify(create_response(
            message="If an account with this email exists, a password reset link has been sent.",
            status_code=200
        ))
        
    except ValueError as e:
        return jsonify(create_response(
            error=str(e),
            status_code=400
        ))
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        return jsonify(create_response(
            error="Password reset request failed",
            status_code=500
        ))

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['token', 'new_password', 'new_password_confirm'])
        
        token = data['token']
        new_password = data['new_password']
        new_password_confirm = data['new_password_confirm']
        
        # Validate password
        is_valid, message = AuthManager.validate_password(new_password)
        if not is_valid:
            return jsonify(create_response(
                error=message,
                status_code=400
            ))
        
        # Check password confirmation
        if new_password != new_password_confirm:
            return jsonify(create_response(
                error="Passwords do not match",
                status_code=400
            ))
        
        # Reset password
        success = AuthManager.reset_password(token, new_password)
        
        if success:
            return jsonify(create_response(
                message="Password reset successfully",
                status_code=200
            ))
        else:
            return jsonify(create_response(
                error="Invalid or expired reset token",
                status_code=400
            ))
        
    except ValueError as e:
        return jsonify(create_response(
            error=str(e),
            status_code=400
        ))
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        return jsonify(create_response(
            error="Password reset failed",
            status_code=500
        ))

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    try:
        user = request.current_user
        
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'subscription_type': user['subscription_type'],
            'onboarding_completed': user['onboarding_completed'],
            'google_calendar_connected': user['google_calendar_connected'],
            'notification_preferences': user.get('notification_preferences', {}),
            'subscription_start_date': user.get('subscription_start_date'),
            'subscription_end_date': user.get('subscription_end_date'),
            'created_at': user['created_at']
        }
        
        return jsonify(create_response(
            data={'user': user_data}
        ))
        
    except Exception as e:
        logger.error(f"Get current user failed: {str(e)}")
        return jsonify(create_response(
            error="Failed to get user info",
            status_code=500
        ))

@auth_bp.route('/update-profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user_id = request.current_user['id']
        
        allowed_fields = ['notification_preferences', 'onboarding_completed']
        update_fields = []
        update_values = []
        
        for field in allowed_fields:
            if field in data:
                if field == 'notification_preferences':
                    import json
                    update_fields.append(f"{field} = %s")
                    update_values.append(json.dumps(data[field]))
                else:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])
        
        if not update_fields:
            return jsonify(create_response(
                error="No valid fields to update",
                status_code=400
            ))
        
        # Update user
        from modules.utils.database import db
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(user_id)
        
        db.execute_query(query, update_values, fetch_all=False)
        
        return jsonify(create_response(
            message="Profile updated successfully"
        ))
        
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        return jsonify(create_response(
            error="Profile update failed",
            status_code=500
        ))