#!/home/ywrloefq/virtualenv/public_html/gm_v4/3.9/bin/python3
"""
Test WSGI application using virtualenv
"""
import sys
import os

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def application(environ, start_response):
    """Simple WSGI test"""
    
    status = '200 OK'
    
    # Check Flask
    flask_status = "❌ NOT installed"
    flask_version = ""
    try:
        import flask
        flask_status = "✅ Installed"
        flask_version = flask.__version__
    except ImportError:
        pass
    
    output = f'''
    <html>
    <head><title>WSGI Test</title></head>
    <body>
        <h1>Python WSGI Test</h1>
        <p><strong>Python:</strong> {sys.version}</p>
        <p><strong>Executable:</strong> {sys.executable}</p>
        <p><strong>Flask:</strong> {flask_status} {flask_version}</p>
        <hr>
        <p>If Flask is installed, the main app should work!</p>
        <p><a href="/gm_v4/api/health">Test /api/health</a></p>
    </body>
    </html>
    '''.encode('utf-8')
    
    response_headers = [
        ('Content-type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(output)))
    ]
    
    start_response(status, response_headers)
    return [output]
