from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from hoodr.auth import login_required
from hoodr.db import get_db

bp = Blueprint('defect', __name__)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    #TODO: avoid sql injection
    qfilter = []
    if request.method == 'POST':
        username = request.form['username']
        defect = request.form['defect']
        category = request.form['category']
        if username:
            qfilter.append("username like '%{}%'".format(username))
        if defect:
            qfilter.append("defect like '%{}%'".format(defect))
        if category:
            qfilter.append("category like '%{}%'".format(category))
    
    sqltext = '''SELECT p.id, defect, details, category, resolution, created, author_id, username
                 FROM post p JOIN user u ON p.author_id = u.id
              '''
    if len(qfilter):
        sqltext = sqltext + ' WHERE ' + ' AND '.join(qfilter)
    sqltext = sqltext + ' ORDER BY created DESC'
    #print(sqltext)

    db = get_db()
    posts = db.execute(sqltext).fetchall()
    return render_template('defect/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        defect = request.form['defect']
        details = request.form['details']
        category = request.form['category']
        resolution = request.form['resolution']
        error = None

        if not defect:
            error = 'Mangel ist ein Pflichtfeld.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (defect, details, category, resolution, author_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (defect, details, category, resolution, g.user['id'])
            )
            db.commit()
            return redirect(url_for('defect.index'))

    return render_template('defect/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, defect, details, category, resolution, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        defect = request.form['defect']
        details = request.form['details']
        category = request.form['category']
        resolution = request.form['resolution']
        error = None

        if not defect:
            error = 'Mangel ist ein Pflichtfeld.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET defect = ?, details = ?, category = ?, resolution = ?'
                ' WHERE id = ?',
                (defect, details, category, resolution, id)
            )
            db.commit()
            return redirect(url_for('defect.index'))

    return render_template('defect/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('defect.index'))