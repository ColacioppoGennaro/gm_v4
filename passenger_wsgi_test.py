#!/home/ywrloefq/virtualenv/public_html/gm_v4/3.9/bin/python3

def application(environ, start_response):
    status = '200 OK'
    output = b'PASSENGER FUNZIONA! Se vedi questo, il problema e\' nell\'import di Flask.'
    
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    
    return [output]
