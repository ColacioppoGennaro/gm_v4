"""
Main Flask application for SmartLife Organizer
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import sys
import os
from datetime import datetime

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

# Import routes
from modules.routes.auth import auth_bp
from modules.routes.events import events_bp
from modules.routes.ai import ai_bp

def create_app():
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
    
    # Debug endpoint - TEST DATABASE
    @app.route('/api/debug/db-test', methods=['GET'])
    def debug_db_test():
        """Test database connection and query"""
        try:
            from modules.utils.database import db
            
            # Test simple query
            result = db.execute_query("SELECT DATABASE() as db_name", fetch_one=True)
            
            # Test events table structure
            columns = db.execute_query("DESCRIBE events", fetch_all=True)
            
            # Test events query
            user_id = '272b4063-9611-4b50-8359-dcef4907e132'
            query = """
                SELECT 
                    e.*,
                    c.name as category_name,
                    c.color as category_color,
                    c.icon as category_icon
                FROM events e
                LEFT JOIN categories c ON e.category_id = c.id
                WHERE e.user_id = %s AND e.deleted_at IS NULL
                ORDER BY e.start_time DESC
            """
            events = db.execute_query(query, [user_id], fetch_all=True)
            
            return jsonify({
                'success': True,
                'database': result,
                'columns': columns,
                'events_count': len(events) if events else 0,
                'events': events
            })
        except Exception as e:
            import traceback
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
    
    # Debug routes endpoint
    @app.route('/api/debug/routes', methods=['GET'])
    def debug_routes():
        """List all registered routes"""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        return jsonify({
            'success': True,
            'routes': sorted(routes, key=lambda x: x['path']),
            'total': len(routes)
        })
    
    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React frontend or API"""
        # If path starts with 'api/', it's handled by blueprints (404 if not found)
        if path.startswith('api/'):
            return jsonify({
                'error': 'API endpoint not found',
                'path': path
            }), 404
        
        # Serve static files from frontend/dist
        from flask import send_from_directory, send_file
        import os
        import mimetypes
        
        frontend_dir = os.path.join(os.path.dirname(__file__), 'static')
        
        # If path is empty, serve index.html
        if path == '':
            index_path = os.path.join(frontend_dir, 'index.html')
            if os.path.exists(index_path):
                return send_file(index_path, mimetype='text/html')
        
        # Try to serve the requested file with correct MIME type
        file_path = os.path.join(frontend_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Get MIME type
            mimetype, _ = mimetypes.guess_type(file_path)
            
            # Ensure correct MIME types for common files
            if path.endswith('.js'):
                mimetype = 'application/javascript'
            elif path.endswith('.css'):
                mimetype = 'text/css'
            elif path.endswith('.json'):
                mimetype = 'application/json'
            elif path.endswith('.html'):
                mimetype = 'text/html'
            
            return send_file(file_path, mimetype=mimetype)
        
        # Fallback to index.html for SPA routing (only for non-asset paths)
        if not path.startswith('assets/'):
            index_path = os.path.join(frontend_dir, 'index.html')
            if os.path.exists(index_path):
                return send_file(index_path, mimetype='text/html')
        
        # If frontend doesn't exist, show API info
        return jsonify({
            'message': 'SmartLife Organizer API v4.0',
            'status': 'running',
            'frontend': 'not found',
            'path': path,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
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