"""
Main Flask application for SmartLife Organizer
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

    # Import routes
    from modules.routes.auth import auth_bp
    from modules.routes.events import events_bp
    from modules.routes.ai import ai_bpdef create_app():
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    from config import Config
    app.config.from_object(Config)
    
    # Set debug logging
    app.logger.setLevel(logging.DEBUG)
    
    # Enable CORS for all origins (restrict in production)
    CORS(app, origins=["*"], supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    
    # Global error handler - CATCH ALL EXCEPTIONS
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception("⚠️ UNHANDLED EXCEPTION:")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'type': type(e).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '4.0.0',
            'service': 'SmartLife Organizer API'
        })
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint"""
        return jsonify({
            'message': 'SmartLife Organizer API v4.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Endpoint not found',
            'success': False,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 'Method not allowed',
            'success': False,
            'timestamp': datetime.utcnow().isoformat()
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'success': False,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)