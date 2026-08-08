from flask import Blueprint, request, jsonify

# from extensions import db
from models import Program, ClassSchedule


time_filter_bp = Blueprint('time_filter', __name__)


@time_filter_bp.route('/get_class_by_time')
def get_class_by_time():
    """
    Finding a specific class based on Program Name, Section, and Time Slot.
    """
    program_name = request.args.get('program')
    section = request.args.get('section')
    time_str = request.args.get('time')

    if not all([program_name, section, time_str]):
        return jsonify({"error": "Program, section, and time are required"}), 400

    try:
        # 1. Find the Program object by its name
        program_obj = Program.query.filter_by(name=program_name).first()
        if not program_obj:
            return jsonify({"status": "Free Period", "reason": "Program not found"})

        # 2. Use the program's ID to find the class
        cls = ClassSchedule.query.filter_by(
            program_id=program_obj.id,
            section=section,
            time_slot=time_str
        ).first()

        if cls:
            # Convert the DB object to a dictionary
            found_class = {
                "Day": cls.day,
                "Time": cls.time_slot,
                "Subject": cls.subject,
                "Room": cls.room
            }
            return jsonify(found_class)
        else:
            return jsonify({"status": "Free Period"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@time_filter_bp.route('/get_day_schedule')
def get_day_schedule():
    """
    Gets the full schedule for a specific program, section, and day.
    (This is needed by index.html)
    """
    program_name = request.args.get('program')
    section = request.args.get('section')
    day = request.args.get('day')

    if not all([program_name, section, day]):
        return jsonify({"error": "Program, section, and day are required"}), 400

    try:
        program_obj = Program.query.filter_by(name=program_name).first()
        if not program_obj:
            return jsonify({"error": "Program not found"}), 404

        schedule_data = ClassSchedule.query.filter_by(
            program_id=program_obj.id,
            section=section,
            day=day
        ).order_by(ClassSchedule.time_slot).all()

        results_list = []
        for cls in schedule_data:
            results_list.append({
                "Day": cls.day,
                "Time": cls.time_slot,
                "Subject": cls.subject,
                "Room": cls.room
            })

        return jsonify(results_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
