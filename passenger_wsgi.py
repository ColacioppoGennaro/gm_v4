#!/home/ywrloefq/virtualenv/public_html/gm_v4/3.9/bin/python3
"""
Passenger WSGI entry point for cPanel hosting
"""
import sys
import os

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'backend'))

# Change to app directory
os.chdir(current_dir)

# Import Flask app from backend/app.py
try:
    # Import the create_app function and create app instance
    sys.path.insert(0, os.path.join(current_dir, 'backend'))
    from app import create_app
    application = create_app()
except ImportError as e:
    # Fallback: show error
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type','text/plain')])
        msg = f'Error importing Flask app: {str(e)}\nPython path: {sys.path}'.encode('utf-8')
        return [msg]

if __name__ == '__main__':
    application.run()