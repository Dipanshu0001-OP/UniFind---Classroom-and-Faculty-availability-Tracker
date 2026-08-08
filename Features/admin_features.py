from flask import Blueprint, request, render_template, redirect, url_for, session, flash
import io
import csv
import json
import os  # Make sure 'os' is imported
from datetime import datetime
from extensions import db
from models import Program, ClassSchedule
from data_processing import parse_timetables_with_headers

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
ADMIN_PASSWORD = "admin123"

# --- THIS IS THE FIX ---
# Get the full path of the current file's directory (e.g., .../features)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get the project's root directory
project_root = os.path.dirname(current_dir)
# Define the path to locations.json in the root
LOCATION_FILE = os.path.join(project_root, 'locations.json')


# ------------------------

@admin_bp.route('/', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Wrong password!', 'danger')

    return render_template('admin.html', logged_in=False)


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard. Shows all programs and the upload forms."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    all_programs = Program.query.order_by(Program.name).all()

    return render_template('admin.html', logged_in=True, programs=all_programs)


@admin_bp.route('/upload_new', methods=['POST'])
def upload_new():
    """Handles the 'Add New Program' form."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    program_name = request.form.get('program_name')
    file = request.files.get('timetable_file')

    if not program_name or not file:
        flash('New program name and file are both required.', 'danger')
        return redirect(url_for('admin.dashboard'))

    existing_program = Program.query.filter_by(name=program_name).first()
    if existing_program:
        flash(f'Program "{program_name}" already exists. Use the update form instead.', 'warning')
        return redirect(url_for('admin.dashboard'))

    try:
        new_program_entry = Program(name=program_name, last_updated=datetime.utcnow())
        db.session.add(new_program_entry)

        in_memory_file = io.BytesIO(file.read())
        timetables = parse_timetables_with_headers(in_memory_file)

        for section_name, classes in timetables.items():
            for class_data in classes:
                new_class_entry = ClassSchedule(
                    section=section_name,
                    day=class_data['Day'],
                    time_slot=class_data['Time'],
                    subject=class_data['Subject'],
                    room=class_data['Room'],
                    program=new_program_entry
                )
                db.session.add(new_class_entry)

        db.session.commit()
        flash(f'Successfully added new program: {program_name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/update_existing', methods=['POST'])
def update_existing():
    """Handles the 'Update Existing Program' form."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    program_id = request.form.get('program_id')
    file = request.files.get('timetable_file')

    if not program_id or not file:
        flash('You must select a program and a file.', 'danger')
        return redirect(url_for('admin.dashboard'))

    try:
        program_to_edit = Program.query.get(program_id)
        if not program_to_edit:
            flash('Program not found.', 'danger')
            return redirect(url_for('admin.dashboard'))

        ClassSchedule.query.filter_by(program_id=program_to_edit.id).delete()

        in_memory_file = io.BytesIO(file.read())
        timetables = parse_timetables_with_headers(in_memory_file)

        for section_name, classes in timetables.items():
            for class_data in classes:
                new_class_entry = ClassSchedule(
                    section=section_name,
                    day=class_data['Day'],
                    time_slot=class_data['Time'],
                    subject=class_data['Subject'],
                    room=class_data['Room'],
                    program_id=program_to_edit.id
                )
                db.session.add(new_class_entry)

        program_to_edit.last_updated = datetime.utcnow()

        db.session.commit()
        flash(f'Successfully updated timetable for {program_to_edit.name}!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


# --- NEW ROUTES FOR ROOM LOCATION MANAGEMENT ---

@admin_bp.route('/manage_rooms', methods=['GET'])
def manage_rooms():
    """
    Shows the new page for managing room locations.
    It loads the current locations from the JSON file to display them.
    """
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    current_locations = {}
    try:
        with open(LOCATION_FILE, 'r') as f:
            current_locations = json.load(f)
    except FileNotFoundError:
        pass  # It's okay if the file doesn't exist yet

    # We pass the dictionary's items to the template so we can loop
    return render_template('admin_rooms.html', locations=current_locations.items())


@admin_bp.route('/upload_rooms_csv', methods=['POST'])
def upload_rooms_csv():
    """
    Handles the .csv file upload. Reads the CSV, converts it to JSON,
    and saves it as locations.json.
    """
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    file = request.files.get('room_file')
    if not file or not file.filename.endswith('.csv'):
        flash('A .csv file is required.', 'danger')
        return redirect(url_for('admin.manage_rooms'))

    room_directory = {}
    try:
        # Read the file as a string
        file.stream.seek(0)
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)

        # Use csv.DictReader to read the CSV rows as dictionaries
        csv_reader = csv.DictReader(stream)

        for row in csv_reader:
            room_name = row.get('room_name')
            if room_name:
                # Store the location details, keyed by the room_name
                room_directory[room_name] = {
                    "building": row.get('building'),
                    "floor": row.get('floor')
                }

        # Write the new directory to the locations.json file
        with open(LOCATION_FILE, 'w') as f:
            json.dump(room_directory, f, indent=4)

        flash('Room Directory updated successfully!', 'success')

    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')

    return redirect(url_for('admin.manage_rooms'))
