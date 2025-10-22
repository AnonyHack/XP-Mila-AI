import logging
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from config import PORT

logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    """Run a simple HTTP server to respond to health checks."""
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"🌐 Health server started on port {PORT}")
    server.serve_forever()

def start_keep_alive():
    """Start the keep-alive system with health server and periodic pings."""
    # Start health server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Periodic pings to keep the server alive
    session = requests.Session()
    while True:
        try:
            # Ping the local health endpoint
            session.get(f'http://localhost:{PORT}/ping', timeout=5)
            # Ping an external service
            session.get('https://www.google.com', timeout=5)
            logger.info("Keep-alive ping successful")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)  # Ping every 5 minutes