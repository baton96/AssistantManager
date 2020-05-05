from flask import Flask, render_template, request, session, redirect, url_for, flash, send_from_directory
#from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_seeder import FlaskSeeder
from flask_migrate import Migrate
from flask_caching import Cache
from PIL import Image
import requests
import os

app = Flask(__name__)
app.secret_key = b'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assistants.db'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_DEFAULT_TIMEOUT'] = '300'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CACHE_TYPE'] = 'simple'

cache = Cache(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
seeder = FlaskSeeder(app, db)
departments = {'IT', 'Managment', 'HR', 'PR'}

class Assistant(db.Model):
    __tablename__ = 'assistants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    department = db.Column(db.String)
    job = db.Column(db.String)


@cache.cached(timeout=50, key_prefix='jobs')
def getJobs():
    url = 'http://api.dataatwork.org/v1/jobs?limit=15'
    req = requests.get(url)
    jobs = {obj['title'] for obj in req.json()[:-1]}
    return jobs

@app.route('/')
def default():
    return redirect(url_for('index'))

@app.route('/assistants/')
def index():
    assistants = db.session.query(Assistant).all()

    allowedDepartments = [dept for dept in departments if dept in request.args]
    if 0 < len(allowedDepartments) < len(departments):
        assistants = [a for a in assistants if a.department in allowedDepartments]

    sortBy = request.args.get('sortBy')
    if sortBy:
        desc = ('desc' in request.args)
        assistants = sorted(
            assistants,
            key=lambda assistant: getattr(assistant, sortBy),
            reverse=desc)

    return render_template('index.html',
                           assistants=assistants,
                           departments=departments)


@app.route('/assistants/create/')
def createForm():
    return render_template('details.html',
                           assistant=Assistant(),
                           departments=departments,
                           jobs=getJobs())


@app.route('/assistants/<int:assistant_id>/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/assistants/', methods=['POST'])
@app.route('/assistants/update/')
def assistantController(assistant_id=None):
    if request.method == 'POST' and request.form.get('_method'):
        method = request.form['_method']
    else:
        method = request.method

    if method == 'POST':
        assistant = Assistant()
    else:
        if not assistant_id:
            assistant_id = request.args['assistant_id']
        assistant = db.session.query(Assistant).get(assistant_id)

    if method in ('POST', 'PUT'):  # TODO validation
        ### db part
        assistant.name = request.form['name']
        assistant.department = request.form['department']
        assistant.job = request.form['job']

    if method == 'GET':
        return render_template('details.html',
                               _method='PUT',
                               assistant=assistant,
                               departments=departments - {assistant.department},
                               jobs=getJobs() - {assistant.job})
    elif method == 'POST':
        db.session.add(assistant)
    elif method == 'DELETE':
        db.session.delete(assistant)
    db.session.commit()

    if method in ('POST', 'PUT'):  # TODO validation
        ### image part
        filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{assistant.id}.jpg')
        thumbnailname = os.path.join(app.config['UPLOAD_FOLDER'], f'{assistant.id}thumbnail.jpg')
        size = 256, 256
        if request.files.get('file'):
            file = request.files['file']
            file.save(filename)
            '''
            im = Image.open(filename)
            im.thumbnail(size)
            im.save(thumbnailname)
            '''

        elif method == 'POST':
            url = 'https://thispersondoesnotexist.com/image'
            headers = {'User-Agent': 'My User Agent 1.0'}  # Doesn't work without custom User-Agent
            req = requests.get(url, headers=headers)
            response = req.content
            with open(filename, "wb") as f:
                f.write(response)
            '''
            im = Image.open(filename)
            im.thumbnail(size)
            im.save(thumbnailname)
            '''

    #global canGetFromCache
    #canGetFromCache = False
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=False)