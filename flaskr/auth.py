import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, json
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from werkzeug.exceptions import abort

# initiating blueprint instance
#bp = Blueprint('auth', __name__, url_prefix='/auth')
bp = Blueprint('auth', __name__)

# run before rendering view
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    #print("user_id: " + str(user_id))

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM user WHERE id = %s', (user_id,))
        user=cursor.fetchone()
        #print(user)
        g.user = user['username']
        g.role = user['role']
        g.user_id = user['id']
        #print(g.user + " - " +  g.role + " - " + str(g.user_id))

# decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/auth', methods=('GET', 'POST'))
@login_required
def index():
    if not "user_filter" in session:
        searchStr = ""
    else:
        searchStr = session["user_filter"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT username, role FROM user '
              +
            searchStr + ") AS users"
            )
    
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')

    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 

        searchUsername = request.form['searchUsername']
        searchRole = request.form['searchRole']
        current_app.logger.debug("searchUsername: " + searchUsername)
        current_app.logger.debug("searchRole: " + searchRole)

        if ((searchUsername + searchRole) != ""):
            searchStr = " WHERE "
        else:
            searchStr = ""
        if (searchUsername != ""):
            searchStr = searchStr + "username LIKE  '%" + searchUsername +"%'"
        if (searchRole != ""):
            if (searchRole != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " role LIKE '%" + searchRole.upper() + "%'"
        current_app.logger.debug("searchStr: " + searchStr)
        #print("searchStr: " + searchStr)
        session["user_filter"] = searchStr

        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT username, role FROM user '
              +
            searchStr + ") AS users"
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    current_app.logger.debug("total: " + str(total))   
    if page == None:
        page = 1
    offset = (int(page)-1) * per_page
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    print(str(per_page) + " ----- " + str(offset))
    cursor.execute(
            'SELECT id, username, role FROM user ' +
             searchStr +
            ' ORDER BY username ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
    users = cursor.fetchall()
    
    return render_template('auth/index.html', users=users, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/auth/register', methods=('GET', 'POST'))
def register():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None

        if not username:
            error = 'Username è obbligatorio.'
        elif not password:
            error = 'Password è obbligatorio.'
        else:
            cursor.execute(
                'SELECT id FROM user WHERE username = %s', (username,))
            row = cursor.fetchone() 
            
        if row != None:
            error = 'User {} è già registrato.'.format(username)

        if error is None:
            #print(len(generate_password_hash(password)))
            cursor.execute('INSERT INTO user (username, password, role) VALUES (%s, %s, %s)',
                (username, generate_password_hash(password), role))
            rs = cursor.fetchall()
            db.commit() # save the changes 
            return redirect(url_for("calendar.show_cal"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/auth/<int:id>/update', methods=('GET', 'POST'))
def update(id): 
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("auth.index"))
    user = get_user(id)

    if request.method == 'POST':
        #username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None

        if (not password) or (not role):
            error = 'Password e ruolo sono obbligatori.'
        
        if error is None:
            cursor.execute('UPDATE user SET password = %s, role = %s'
                           ' WHERE id = %s',
                    (generate_password_hash(password), role, id))
            db.commit()
            return redirect(url_for("auth.index"))

        flash(error)

    return render_template('auth/update.html', user=user)

@bp.route('/auth/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("auth.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM user WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('auth.index'))

@bp.route('/auth/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        error = None
        cursor.execute(
            'SELECT * FROM user WHERE username = %s', (username,)
        )
        user = cursor.fetchone()
        #print(user)
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('home.index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def get_user(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, username, role FROM user'
        ' WHERE id = %s',
        (id,)
    )
    user = cursor.fetchone()
    print(user)
    
    if user is None:
        abort(404, f"user id {id} non esiste.")

    return user