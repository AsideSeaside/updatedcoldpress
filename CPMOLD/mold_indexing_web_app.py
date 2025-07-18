# mold_indexing_web_app

This Flask application lets users search molds/parts by part number or mold number, view cycle time, process media (images/videos), bill of materials, and number of operators. Users can also add new molds individually or bulk-upload via Excel.

## Tech Stack
- Python 3.9+
- Flask
- SQLAlchemy (with SQLite for local / Cloud SQL for production)
- Google Cloud Storage (for media)
- pandas (for Excel ingestion)
- Bootstrap 5 (for UI)

## Directory Structure
```
mold_app/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   └── detail.html
└── static/
    └── css/
        └── style.css
``` 

---

# requirements.txt
```
Flask
SQLAlchemy
pandas
openpyxl
google-cloud-storage
python-dotenv
``` 

---

# config.py
```python
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///molds.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GCS_BUCKET = os.getenv("GCS_BUCKET")  # e.g. 'my-media-bucket'
    # Ensure GOOGLE_APPLICATION_CREDENTIALS is set to your service account key JSON
``` 

---

# models.py
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Mold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_number = db.Column(db.String(50), unique=True, nullable=False)
    mold_number = db.Column(db.String(50), unique=True, nullable=False)
    cycle_time = db.Column(db.Float, nullable=False)
    bom = db.Column(db.Text, nullable=False)  # JSON or newline-separated items
    num_operators = db.Column(db.Integer, nullable=False)
    media = db.relationship('Media', backref='mold', lazy=True)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mold_id = db.Column(db.Integer, db.ForeignKey('mold.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
``` 

---

# app.py
```python
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from google.cloud import storage
import pandas as pd
from config import Config
from models import db, Mold, Media

# Initialize Flask
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret')

# Initialize DB
db.init_app(app)
with app.app_context():
    db.create_all()

# Initialize GCS client
gcs_client = storage.Client()
bucket = gcs_client.bucket(app.config['GCS_BUCKET'])

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}


def upload_to_gcs(file_obj, destination):
    blob = bucket.blob(destination)
    blob.upload_from_file(file_obj)
    blob.make_public()
    return blob.public_url

@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.form.get('query')
    molds = []
    if query:
        molds = Mold.query.filter(
            (Mold.part_number == query) | (Mold.mold_number == query)
        ).all()
    return render_template('index.html', molds=molds)

@app.route('/mold/<int:mold_id>')
def detail(mold_id):
    mold = Mold.query.get_or_404(mold_id)
    return render_template('detail.html', mold=mold)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # single entry
        part_number = request.form['part_number']
        mold_number = request.form['mold_number']
        cycle_time = float(request.form['cycle_time'])
        bom = request.form['bom']
        num_ops = int(request.form['num_operators'])

        mold = Mold(
            part_number=part_number,
            mold_number=mold_number,
            cycle_time=cycle_time,
            bom=bom,
            num_operators=num_ops
        )
        db.session.add(mold)
        db.session.commit()

        # handle media files
        files = request.files.getlist('media')
        for f in files:
            ext = f.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_EXT:
                fname = secure_filename(f.filename)
                dest = f"mold_{mold.id}/{fname}"
                url = upload_to_gcs(f, dest)
                mtype = 'video' if ext in {'mp4', 'mov'} else 'image'
                media = Media(mold_id=mold.id, url=url, media_type=mtype)
                db.session.add(media)
        db.session.commit()

        flash('Mold added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    if request.method == 'POST':
        file = request.files['excel']
        df = pd.read_excel(file)
        for _, row in df.iterrows():
            mold = Mold(
                part_number=row['part_number'],
                mold_number=row['mold_number'],
                cycle_time=row['cycle_time'],
                bom=row['bom'],
                num_operators=int(row['num_operators'])
            )
            db.session.add(mold)
        db.session.commit()
        flash('Bulk upload complete!', 'success')
        return redirect(url_for('index'))
    return render_template('bulk_upload.html')

if __name__ == '__main__':
    app.run(debug=True)
``` 

---

# templates/base.html
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <title>Mold Index</title>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
  <div class="container-fluid">
    <a class="navbar-brand" href="{{ url_for('index') }}">Mold Index</a>
    <div>
      <a class="btn btn-outline-primary me-2" href="{{ url_for('add') }}">Add Mold</a>
      <a class="btn btn-outline-secondary" href="{{ url_for('bulk_upload') }}">Bulk Upload</a>
    </div>
  </div>
</nav>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, msg in messages %}
        <div class="alert alert-{{ category }}">{{ msg }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
</body>
</html>
``` 

---

# templates/index.html
```html
{% extends 'base.html' %}
{% block content %}
  <form method="post" class="mb-3">
    <div class="input-group">
      <input type="text" name="query" class="form-control" placeholder="Search by part or mold number">
      <button class="btn btn-primary" type="submit">Search</button>
    </div>
  </form>
  {% if molds %}
    <ul class="list-group">
      {% for m in molds %}
        <li class="list-group-item">
          <a href="{{ url_for('detail', mold_id=m.id) }}">{{ m.part_number }} / {{ m.mold_number }}</a>
        </li>
      {% endfor %}
    </ul>
  {% endif %}
{% endblock %}
``` 

---

# templates/detail.html
```html
{% extends 'base.html' %}
{% block content %}
  <h2>{{ mold.part_number }} / {{ mold.mold_number }}</h2>
  <p><strong>Cycle Time:</strong> {{ mold.cycle_time }} s</p>
  <p><strong>Operators:</strong> {{ mold.num_operators }}</p>
  <p><strong>BOM:</strong><br>{{ mold.bom.replace('\n','<br>')|safe }}</p>
  <div class="row">
    {% for media in mold.media %}
      <div class="col-md-4 mb-3">
        {% if media.media_type=='image' %}
          <img src="{{ media.url }}" class="img-fluid" />
        {% else %}
          <video src="{{ media.url }}" controls class="w-100"></video>
        {% endif %}
      </div>
    {% endfor %}
  </div>
{% endblock %}
