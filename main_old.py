from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess

HOST = "192.168.50.20"

PORT = 9999

class MaxHTTP(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.log_request_info()
        external_output = self.call_external_script()
        self.parse_request()



        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        message = f"{external_output}"
        print(f"{message}")
        self.wfile.w
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess

HOST = "192.168.50.20"

PORT = 9999

class MaxHTTP(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.log_request_info()
        external_output = self.call_external_script()
        self.parse_request()



        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        message = f"{external_output}"
        print(f"{message}")
        self.wfile.w