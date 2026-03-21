import http.server
import socketserver
import os
import sys

PORT = 8000

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect root to research_ui/index.html
        if self.path == '/' or self.path == '':
            self.path = '/research_ui/index.html'
        return super().do_GET()

def run_server():
    # Ensure we are in the project root (where outputs/ and research_ui/ are)
    # The user might run this from project_root or research_ui/
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "research_ui":
        os.chdir("..")
        print("Changed directory to project root.")
    
    print(f"\n--- QuantLab Research Dashboard Dev Server ---")
    print(f"Serving from: {os.getcwd()}")
    print(f"Mode: Local Dev-Preview Only")
    print(f"URL: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop\n")

    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == "__main__":
    run_server()
