#!/usr/bin/env python3
"""
Simple test file to verify Python is working
"""

def application(environ, start_response):
    """WSGI application for testing"""
    status = '200 OK'
    
    output = b'''
    <html>
    <head><title>Python Test</title></head>
    <body>
        <h1>Python is Working!</h1>
        <p>Environment: Production</p>
        <p>If you see this, Python/WSGI is configured correctly.</p>
    </body>
    </html>
    '''
    
    response_headers = [
        ('Content-type', 'text/html'),
        ('Content-Length', str(len(output)))
    ]
    
    start_response(status, response_headers)
    return [output]

if __name__ == '__main__':
    print("Test OK")
