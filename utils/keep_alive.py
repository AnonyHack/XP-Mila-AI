import logging
import time
import requests
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from config import PORT, BOT_TOKEN, API_ID, API_HASH
from datetime import datetime

logger = logging.getLogger(__name__)

def load_template():
    """Load the HTML template from file."""
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'status.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        return "<h1>Bot Status</h1><p>Template loading failed</p>"

class HealthHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.template = load_template()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        logger.info(f"Received request for: {self.path}")
        if self.path == '/ping':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            # Determine if we're in production (Koyeb) or local
            is_production = os.environ.get('RENDER_APP_NAME') is not None
            
            # Prepare template variables
            template_vars = {
                'bot_status': '🟢 Online',
                'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'server_info': 'Render Cloud' if is_production else 'Local Development',
                'port': PORT,
                'api_id_display': 'Configured' if API_ID else 'Not set',
                'api_hash_display': '*' * 20 if API_HASH else 'Not set',
                'bot_token_display': BOT_TOKEN[:10] + '...' + BOT_TOKEN[-5:] if BOT_TOKEN and len(BOT_TOKEN) > 15 else 'Not set',
                'deployment_info': 'Production Deployment' if is_production else 'Local Development Server'
            }
            
            # Render template
            html_content = self.template
            for key, value in template_vars.items():
                html_content = html_content.replace('{{' + key + '}}', str(value))
            
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 - Page not found")

    def is_bot_running(self):
        """Check if the bot is running."""
        return True

    def log_message(self, format, *args):
        """Override to reduce log noise."""
        logger.info(f"HTTP {self.command} {self.path} - {self.client_address[0]}")

def run_health_server():
    """Run a simple HTTP server to respond to health checks and display bot info."""
    try:
        # Use localhost for development, 0.0.0.0 for production
        host = '0.0.0.0' if os.environ.get('RENDER_APP_NAME') else 'localhost'
        server = HTTPServer((host, PORT), HealthHandler)
        
        if os.environ.get('RENDER_APP_NAME'):
            logger.info(f"🌐 Production health server started on port {PORT}")
            logger.info(f"💖 MILA AI Girlfriend is live!")
        else:
            logger.info(f"🌐 Development health server started on port {PORT}")
            logger.info(f"💖 MILA AI Girlfriend status: http://localhost:{PORT}/")
        
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        raise

def start_keep_alive():
    """Start the keep-alive system with health server and periodic pings."""
    # Start health server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("Health server thread started")
    
    # Periodic pings to keep the server alive
    session = requests.Session()
    while True:
        try:
            # Ping the local health endpoint
            host = 'localhost' if not os.environ.get('RENDER_APP_NAME') else '0.0.0.0'
            response = session.get(f'http://{host}:{PORT}/ping', timeout=5)
            logger.debug(f"Keep-alive ping successful: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)  # Ping every 5 minutes
