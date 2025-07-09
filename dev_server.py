#!/usr/bin/env python3
"""
Development server with proper cache headers for GitHub integration testing
"""
import http.server
import socketserver
import os
from datetime import datetime

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-Timestamp', str(datetime.now().timestamp()))
        super().end_headers()

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

if __name__ == "__main__":
    PORT = 8005
    
    # Change to the frontend/public directory
    web_dir = "/home/ghost/engunity/frontend/public"
    os.chdir(web_dir)
    
    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print(f"🚀 Development server starting at http://localhost:{PORT}")
        print(f"📁 Serving files from: {web_dir}")
        print(f"🔄 Cache-Control: no-cache (fresh files every request)")
        print(f"🌐 GitHub Integration: http://localhost:{PORT}/pages/github-integration.html")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")