

import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
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

# Local media storage setup
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_file_locally(file_obj, destination):
    """Save uploaded file to local storage and return the URL path"""
    file_path = os.path.join(UPLOAD_FOLDER, destination)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_obj.save(file_path)
    return f"/static/uploads/{destination}"

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

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
            if f.filename:
                ext = f.filename.rsplit('.', 1)[-1].lower()
                if ext in ALLOWED_EXT:
                    fname = secure_filename(f.filename)
                    dest = f"mold_{mold.id}/{fname}"
                    try:
                        url = save_file_locally(f, dest)
                        mtype = 'video' if ext in {'mp4', 'mov'} else 'image'
                        media = Media(mold_id=mold.id, url=url, media_type=mtype)
                        db.session.add(media)
                        flash(f'Successfully uploaded {fname}', 'success')
                    except Exception as e:
                        flash(f'Error uploading {fname}: {str(e)}', 'error')
        db.session.commit()

        flash('Mold added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/show_all')
def show_all():
    molds = Mold.query.all()
    return render_template('show_all.html', molds=molds)

@app.route('/edit_database')
def edit_database():
    molds = Mold.query.all()
    return render_template('edit_database.html', molds=molds)

@app.route('/edit_mold/<int:mold_id>', methods=['GET', 'POST'])
def edit_mold(mold_id):
    mold = Mold.query.get_or_404(mold_id)
    if request.method == 'POST':
        mold.part_number = request.form['part_number']
        mold.mold_number = request.form['mold_number']
        mold.cycle_time = float(request.form['cycle_time'])
        mold.bom = request.form['bom']
        mold.num_operators = int(request.form['num_operators'])
        
        # Handle new media files
        files = request.files.getlist('media')
        for f in files:
            if f.filename:
                ext = f.filename.rsplit('.', 1)[-1].lower()
                if ext in ALLOWED_EXT:
                    fname = secure_filename(f.filename)
                    dest = f"mold_{mold.id}/{fname}"
                    try:
                        url = save_file_locally(f, dest)
                        mtype = 'video' if ext in {'mp4', 'mov'} else 'image'
                        media = Media(mold_id=mold.id, url=url, media_type=mtype)
                        db.session.add(media)
                        flash(f'Successfully uploaded {fname}', 'success')
                    except Exception as e:
                        flash(f'Error uploading {fname}: {str(e)}', 'error')
        
        db.session.commit()
        flash('Mold updated successfully!', 'success')
        return redirect(url_for('edit_database'))
    return render_template('edit_mold.html', mold=mold)

@app.route('/delete_mold/<int:mold_id>', methods=['POST'])
def delete_mold(mold_id):
    mold = Mold.query.get_or_404(mold_id)
    # Delete associated media files
    for media in mold.media:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, media.url.replace('/static/uploads/', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            flash(f'Error deleting media file: {str(e)}', 'warning')
    
    db.session.delete(mold)
    db.session.commit()
    flash('Mold deleted successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/delete_media/<int:media_id>', methods=['POST'])
def delete_media(media_id):
    media = Media.query.get_or_404(media_id)
    mold_id = media.mold_id
    
    # Delete the file
    try:
        file_path = os.path.join(UPLOAD_FOLDER, media.url.replace('/static/uploads/', ''))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Error deleting media file: {str(e)}', 'warning')
    
    db.session.delete(media)
    db.session.commit()
    flash('Media deleted successfully!', 'success')
    return redirect(url_for('edit_mold', mold_id=mold_id))

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
    app.run(host='0.0.0.0', port=3000, debug=True)

