#!/usr/bin/env python3
"""
Passenger WSGI entry point for cPanel hosting
This file is required by Phusion Passenger to run the Flask app
"""

import sys
import os

# Add the backend directory to Python path
INTERP = "/usr/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'backend'))

# Change working directory
os.chdir(current_dir)

# Import Flask app
from backend.app import app as application

# For debugging
if __name__ == '__main__':
    application.run()