from flask import Blueprint, request, jsonify

# --- UPDATED IMPORTS ---
from extensions import db
from models import Program, ClassSchedule

free_room_bp = Blueprint('free_room_finder', __name__)


@free_room_bp.route('/get_free_rooms')
def get_free_rooms():
    """
    Finds all rooms that are not occupied by any program/section at a specific time.
    """
    time_str = request.args.get('time')
    if not time_str:
        return jsonify({"error": "A time must be provided"}), 400

    try:
        # 1. Find all unique rooms in the entire database
        all_rooms_q = db.session.query(ClassSchedule.room).distinct().all()
        # Use a set for efficiency and to auto-handle duplicates
        all_rooms_set = {room[0] for room in all_rooms_q if room[0]}

        # 2. Find all rooms that are occupied at this specific time
        occupied_rooms_q = db.session.query(ClassSchedule.room) \
            .filter_by(time_slot=time_str) \
            .distinct().all()
        occupied_rooms_set = {room[0] for room in occupied_rooms_q if room[0]}

        # 3. Calculate the free rooms using set difference
        free_rooms = all_rooms_set - occupied_rooms_set

        # 4. Clean up the list (remove non-bookable "rooms")
        free_rooms.discard("Online")
        free_rooms.discard("Not Specified")

        return jsonify(sorted(list(free_rooms)))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
