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
    data = None
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
    except Exception as e:
        logging.exception("Error processing asset")
        return jsonify({"error": str(e)}), 500

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
    return send_file(file_path, mimetype="image/png", as_attachment=True, download_name=f"{asset_id}.png")


if __name__ == "__main__":
    # For local development
    app.run(host="127.0.0.1", port=5000, debug=False)
else:
    # For Vercel
    # The app variable will be used by the Vercel Python runtime
