from flask import Flask, render_template, request, jsonify
import os

# --- 1. Import extensions and models ---
from extensions import db
from models import Program, ClassSchedule  # Needed for routes and db.create_all()

# --- 2. App Setup ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

# Config for the database and a secret key for sessions
app.config['SECRET_KEY'] = 'my_college_project_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'university.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 3. Initialize db with the app ---
# connection bw db and extensions
db.init_app(app)

# --- 4. Import and Register Blueprints ---
from features.admin_feature import admin_bp
from features.search_feature import search_bp
from features.time_filter_feature import time_filter_bp
from features.free_room_finder_feature import free_room_bp
from features.location_feature import location_bp  # <-- 1. IMPORT NEW BLUEPRINT

app.register_blueprint(admin_bp)
app.register_blueprint(search_bp)
app.register_blueprint(time_filter_bp)
app.register_blueprint(free_room_bp)
app.register_blueprint(location_bp)  # <-- 2. REGISTER NEW BLUEPRINT


# --- 5. Core API Routes (for the User Dashboard) ---

@app.route('/')
def index():
    """Renders the main HTML page for students."""
    return render_template('index.html')


@app.route('/get_initial_data')
def get_initial_data():

    try:
        programs_from_db = db.session.query(Program.name).distinct().all()
        times_from_db = db.session.query(ClassSchedule.time_slot).distinct().all()

        program_list = []
        for p in programs_from_db:
            program_list.append(p[0])

        time_list = sorted([t[0] for t in times_from_db if t[0]])
        day_list = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        return jsonify({
            "programs": program_list,
            "days": day_list,
            "time_slots": time_list
        })
    except Exception as e:
        return jsonify({"programs": [], "days": [], "time_slots": []})


@app.route('/get_sections_for_program')
def get_sections_for_program():
    """Gets all sections for a selected program."""
    program_name = request.args.get('program')

    program_obj = Program.query.filter_by(name=program_name).first()

    if not program_obj:
        return jsonify([])

    sections_from_db = db.session.query(ClassSchedule.section) \
        .filter_by(program_id=program_obj.id) \
        .distinct().all()

    section_list = []
    for s in sections_from_db:
        section_list.append(s[0])

    return jsonify(section_list)


# --- 6. Run the App ---
if __name__ == '__main__':
    with app.app_context():
        # This looks for all classes that inherited from db.Model (in models.py)
        # and creates them.
        db.create_all()
    app.run(debug=True)
