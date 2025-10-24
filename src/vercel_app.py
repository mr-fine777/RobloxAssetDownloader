from flask import Flask
from web_server import app as flask_app

# Initialize the Flask application
app = flask_app

# Vercel serverless handler
def handler(request):
    """Handle requests in a serverless context."""
    with app.request_context(request):
        try:
            return app.full_dispatch_request()
        except Exception as e:
            app.logger.error(f"Error handling request: {e}")
            return 'Internal Server Error', 500