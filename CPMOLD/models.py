
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(50), unique=True, nullable=False)
    mold_number = db.Column(db.String(50), unique=True, nullable=False)
    cycle_time = db.Column(db.Float, nullable=False)  # stored in minutes
    bom = db.Column(db.Text, nullable=False)  # JSON or newline-separated items
    num_operators = db.Column(db.Integer, nullable=False)
    media = db.relationship('Media', backref='mold', lazy=True)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mold_id = db.Column(db.Integer, db.ForeignKey('mold.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
