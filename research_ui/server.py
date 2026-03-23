import http.server
import socketserver
import os
import sys

PORT = 8000

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect root to research_ui/index.html to ensure relative asset paths work
        if self.path == '/' or self.path == '':
            self.send_response(302)
            self.send_header('Location', '/research_ui/index.html')
            self.end_headers()
            return
        return super().do_GET()

def run_server():
    # Ensure we are in the project root
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "research_ui":
        os.chdir("..")
        print("Changed directory to project root.")
    
    port = PORT
    max_retries = 5
    httpd = None

    while max_retries > 0:
        try:
            httpd = socketserver.TCPServer(("", port), DashboardHandler)
            break
        except OSError:
            print(f"Port {port} is busy, trying {port + 1}...")
            port += 1
            max_retries -= 1

    if not httpd:
        print("Error: Could not find an available port.")
        sys.exit(1)

    print(f"\n--- QuantLab Research Dashboard Dev Server ---")
    print(f"Serving from: {os.getcwd()}")
    print(f"URL: http://localhost:{port}")
    print(f"Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    run_server()
