#!/usr/bin/env python3
"""
CGI entry point for hosting without Passenger
Simple CGI script to run Flask app
"""

import sys
import os
from io import BytesIO

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'backend'))

# Change to app directory
os.chdir(current_dir)

# Import Flask app
from backend.app import app

# CGI handler
from wsgiref.handlers import CGIHandler

if __name__ == '__main__':
    CGIHandler().run(app)