"""
Vercel WSGI entrypoint.

Vercel's Python runtime will look for a WSGI callable named `app`.
We simply re-export the Flask app defined in `src/web_server.py` so the
serverless runtime can invoke it directly.
"""

from web_server import app  # re-export the Flask WSGI application
