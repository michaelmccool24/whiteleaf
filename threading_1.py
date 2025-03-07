import http.server
import socketserver
import threading
import time

PORT = 8080

class ThreadedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Logging
        thread_id = threading.get_ident()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Thread {thread_id} handling request at {current_time}")

        # AI process time
        print(f"Processing request: {thread_id}")
        time.sleep(20)
        

        # Send response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"Handled by Thread {thread_id} at {current_time}".encode())

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def start_server():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), ThreadedHTTPRequestHandler)
    print(f"Server started on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server is shutting down...")