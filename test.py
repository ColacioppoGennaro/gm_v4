#!/usr/bin/env python3
"""
Simple CGI test
"""
print("Content-Type: text/html\n")
print("<html><body>")
print("<h1>Python CGI Works!</h1>")
print("<p>Python version check...</p>")

import sys
print(f"<p>Python: {sys.version}</p>")
print(f"<p>Path: {sys.executable}</p>")

try:
    import flask
    print(f"<p>✅ Flask installed: {flask.__version__}</p>")
except ImportError as e:
    print(f"<p>❌ Flask NOT installed: {e}</p>")

try:
    import pymysql
    print(f"<p>✅ PyMySQL installed</p>")
except ImportError as e:
    print(f"<p>❌ PyMySQL NOT installed: {e}</p>")

print("</body></html>")
