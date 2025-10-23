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
        """Handle GET requests."""
        self.handle_request()

    def do_HEAD(self):
        """Handle HEAD requests (for health checks)."""
        self.handle_request(include_body=False)

    def handle_request(self, include_body=True):
        """Common request handler for both GET and HEAD."""
        logger.info(f"Received {self.command} request for: {self.path}")
        
        if self.path == '/ping':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            if include_body:
                self.wfile.write(b"OK")
                
        elif self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            if include_body:
                # Determine if we're in production (Render) or local
                is_production = os.environ.get('RENDER') is not None
                
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
            if include_body:
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
        # Use 0.0.0.0 for Render to bind to all interfaces
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', PORT))
        
        server = HTTPServer((host, port), HealthHandler)
        
        logger.info(f"🌐 Health server started on {host}:{port}")
        logger.info(f"💖 MILA AI Girlfriend status page is live!")
        logger.info(f"📡 Server binding to all interfaces on port {port}")
        logger.info(f"🔧 Ready to handle GET and HEAD requests")
        
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        # Don't raise the exception, just log it and let the bot continue
        logger.info("Bot will continue without health server")

def start_keep_alive():
    """Start the keep-alive system with health server and periodic pings."""
    try:
        # Start health server in a separate thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        logger.info("Health server thread started successfully")
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Test if the server is responding
        try:
            port = int(os.environ.get('PORT', PORT))
            response = requests.get(f'http://localhost:{port}/ping', timeout=5)
            if response.status_code == 200:
                logger.info("✅ Health server is responding correctly")
            else:
                logger.warning(f"⚠️ Health server returned status: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Health server test failed: {e}")
        
    except Exception as e:
        logger.error(f"Failed to start health server thread: {e}")
        logger.info("Continuing without health server")
    
    # Periodic pings to keep the server alive (only if we're not on Render)
    # On Render, the web service itself keeps it alive
    if not os.environ.get('RENDER'):
        session = requests.Session()
        while True:
            try:
                # Ping the local health endpoint
                port = int(os.environ.get('PORT', PORT))
                response = session.get(f'http://localhost:{port}/ping', timeout=5)
                logger.debug(f"Keep-alive ping successful: {response.status_code}")
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}")
            time.sleep(300)  # Ping every 5 minutes
