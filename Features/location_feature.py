from flask import Blueprint, jsonify
import json
import os # Make sure 'os' is imported

location_bp = Blueprint('location', __name__)

# --- THIS IS THE FIX ---
# Get the full path of the current file's directory (e.g., .../features)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the project's root directory
project_root = os.path.dirname(current_dir)
# Define the path to locations.json in the root
LOCATION_FILE = os.path.join(project_root, 'locations.json')
# ------------------------


@location_bp.route('/get_all_locations')
def get_all_locations():
    """
    Loads the locations.json file and sends it to the frontend.
    """
    try:
        with open(LOCATION_FILE, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except FileNotFoundError:
        # If the admin hasn't uploaded the file yet, just return an empty object
        return jsonify({})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
