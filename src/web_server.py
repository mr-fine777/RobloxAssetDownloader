from flask import Flask, request, send_file, jsonify
import asyncio
import os
import re
import logging

from roblox_asset_downloader import RobloxAssetDownloader

# Minimal Flask app that exposes only the API path used by the front-end.
# The static site should be served by Apache/XAMPP (copy src/static into htdocs).
app = Flask(__name__)


@app.route("/api/download", methods=["POST"])  # API path intended for proxying by Apache
def download_api():
    """Accept a JSON body or form field 'clothing' (ID or URL), process the asset,
    and return the resulting PNG as an attachment.

    This endpoint intentionally does not serve static files so Apache can handle them.
    """
    try:
        # Parse input
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        clothing = data.get("clothing") if isinstance(data, dict) else None
        if not clothing:
            return jsonify({"error": "Please provide clothing id or url in field 'clothing'"}), 400

        # Run the asynchronous processing synchronously for this endpoint
        downloader = RobloxAssetDownloader()
        try:
            asyncio.run(downloader.process_asset(clothing))
        except Exception:
            logging.exception("Error processing asset")
            return jsonify({"error": "Error processing asset"}), 500

        # Determine the numeric asset id from the provided input
        asset_id = re.sub(r"[^0-9]", "", clothing)
        if not asset_id:
            return jsonify({"error": "Could not determine numeric asset id from input"}), 400

        # Determine where files are written. In serverless environments we set
        # DOWNLOADS_DIR (usually /tmp). Fall back to the repo 'downloads/' for
        # local development.
        downloads_dir = os.environ.get(
            "DOWNLOADS_DIR",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads"),
        )
        file_path = os.path.join(downloads_dir, f"{asset_id}.png")

        if not os.path.exists(file_path):
            return jsonify({"error": "Download finished but output file not found"}), 500

        # Return the processed image as an attachment
        return send_file(
            file_path, mimetype="image/png", as_attachment=True, download_name=f"{asset_id}.png"
        )
    except Exception:
        logging.exception("Unhandled exception in download_api")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/download/<asset_id>", methods=["GET"])  # One-click download URL
def download_get(asset_id: str):
    """One-click GET endpoint to download a clothing asset by ID.

    Example: GET /download/81146553878533
    This proxies the same processing as the POST /api/download endpoint
    but accepts the asset id directly in the URL for convenience.
    """
    try:
        # Normalize asset id to digits only
        asset_id_clean = re.sub(r"[^0-9]", "", asset_id)
        if not asset_id_clean:
            return jsonify({"error": "Invalid asset id"}), 400

        # Run the processing (same as POST handler)
        downloader = RobloxAssetDownloader()
        try:
            asyncio.run(downloader.process_asset(asset_id_clean))
        except Exception:
            logging.exception("Error processing asset via GET download")
            return jsonify({"error": "Error processing asset"}), 500

        downloads_dir = os.environ.get(
            "DOWNLOADS_DIR",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads"),
        )
        file_path = os.path.join(downloads_dir, f"{asset_id_clean}.png")

        if not os.path.exists(file_path):
            return jsonify({"error": "Download finished but output file not found"}), 500

        return send_file(
            file_path, mimetype="image/png", as_attachment=True, download_name=f"{asset_id_clean}.png"
        )
    except Exception:
        logging.exception("Unhandled exception in download_get")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # For local development
    app.run(host="127.0.0.1", port=5000, debug=False)
# When imported by a WSGI server (like Vercel's Python runtime) the
# `app` Flask instance defined above will be used directly. No further
# runtime-specific wiring is necessary here.

