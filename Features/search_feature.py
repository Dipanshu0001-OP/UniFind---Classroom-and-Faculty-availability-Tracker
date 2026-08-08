from flask import Blueprint, request, jsonify

# Import from the new files, NOT from app.py
from extensions import db
from models import Program, ClassSchedule

# ------------------------

search_bp = Blueprint('search', __name__)


@search_bp.route('/search_subject')
def search_subject():
    """
    Searches for a subject across all programs and sections.
    """
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({"error": "A search query ('q') is required."}), 400

    try:
        # This is a database JOIN.
        # It queries ClassSchedule and joins it with Program
        # where the subject is like the query.
        search_results = db.session.query(ClassSchedule, Program) \
            .join(Program, ClassSchedule.program_id == Program.id) \
            .filter(ClassSchedule.subject.ilike(f"%{query}%")) \
            .all()

        results_list = []
        for (cls, prog) in search_results:
            results_list.append({
                "Program": prog.name,
                "Section": cls.section,
                "Day": cls.day,
                "Time": cls.time_slot,
                "Subject": cls.subject,
                "Room": cls.room
            })

        return jsonify(results_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
