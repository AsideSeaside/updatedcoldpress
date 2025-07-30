# models.py

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Mold(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    part_number    = db.Column(db.String(50), unique=True, nullable=False)
    mold_number    = db.Column(db.String(50), unique=True, nullable=False)
    cycle_time     = db.Column(db.Float, nullable=False)
    bom            = db.Column(db.Text, nullable=False)
    num_operators  = db.Column(db.Integer, nullable=False)

    # New: store standard & actual times per process
    process_data   = db.Column(db.JSON, nullable=False, default={
        "Prefab":   {"standard": 5.52, "actual": None},
        "Gelcoat":  {"standard": 3.20, "actual": None},
        "Lamination": {"standard":14.09,"actual": None},
        "Foam":     {"standard":   0, "actual": None},
        "Part & Prep": {"standard":4.23,"actual": None},
        "T&G":      {"standard":3.96, "actual": None},
        "Part Inspection": {"standard":0, "actual": None},
        "QC Check": {"standard":0, "actual": None},
        "Mold Repair": {"standard":0, "actual": None},
    })


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mold_id = db.Column(db.Integer, db.ForeignKey('mold.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
