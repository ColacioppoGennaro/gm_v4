#!/usr/bin/env python3
"""
Entry point for SmartLife Organizer Flask application
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)