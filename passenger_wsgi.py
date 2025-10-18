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

# Import Flask app
from backend.app import app as application

if __name__ == '__main__':
    application.run()