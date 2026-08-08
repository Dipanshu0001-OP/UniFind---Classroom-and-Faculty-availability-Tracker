from extensions import db
from datetime import datetime


# This is the Program table.
class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # This links to the ClassSchedule. 'lazy=True' is default but good to show.
    # 'cascade' means if I delete a Program, all its classes get deleted too.
    schedules = db.relationship('ClassSchedule', backref='program', lazy=True, cascade='all, delete-orphan')


# This is the ClassSchedule table.
class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # This is the 'link' to the Program table's 'id' column
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)

    section = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    room = db.Column(db.String(100), nullable=True)
