from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('people', __name__)

@bp.route('/people', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM people')
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    searchStr = ""
    if request.method == 'POST': 
        searchStr = request.form['search']
        searchQ = "%" + searchStr + "%"
        searchQ = searchQ.upper()
        cursor.execute(
            'SELECT COUNT(*) AS count FROM people WHERE CONCAT(surname, " ", name) LIKE %s',
            (searchQ,)
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    if page != None:
        offset = (int(page)-1) * per_page
    else:
        page = "1"
        offset = 0   
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    
    if searchStr == "":
        cursor.execute(
            'SELECT id, CONCAT(surname, " ", name) AS people_name, type, cessato, user_id'
            ' FROM people '
            ' ORDER BY people_name ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
        peoples = cursor.fetchall()
    else:
        searchQ = "%" + searchStr + "%"
        searchQ = searchQ.upper()
        cursor.execute(
            'SELECT id, CONCAT(surname, " ", name) AS people_name, type, cessato, user_id'
            ' FROM people '
            ' WHERE CONCAT(surname, " ", name) LIKE %s'
            ' ORDER BY people_name ASC LIMIT %s OFFSET %s',
            (searchQ, per_page, offset)
        )
        peoples = cursor.fetchall()
    return render_template('people/index.html', peoples=peoples, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/people/create', methods=('GET', 'POST'))
@login_required
def create():
    userList = get_userList()
    people_types = get_people_type()
    if request.method == 'POST':
        surname = request.form['surname']
        name = request.form['name']
        cessato = request.form['cessato']
        type = request.form['input_type']
        if request.form['input_user_id'] == None or request.form['input_user_id'] == "":
            user_id = None
        else:
            user_id = int(request.form['input_user_id'])
        error = None

        if (not surname) or (not name) or (not type):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO people (surname, name, cessato, type, user_id)'
                ' VALUES (%s, %s, %s, %s, %s)',
                (surname, name, cessato, type, user_id)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            id = row['last_insert']
            cursor.execute(
                'INSERT INTO people_payment (people_id)'
                ' VALUES (%s)',
                (id,)
            )
            db.commit()
            return redirect(url_for('people.index'))

    return render_template('people/create.html', userList=userList, people_types=people_types)

@bp.route('/people/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    people = get_people(id)
    userList = get_userList()
    people_types = get_people_type()
    
    if request.method == 'POST':
        surname = request.form['surname']
        name = request.form['name']
        cessato = request.form['cessato']
        type = request.form['input_type']
        gg_paga = request.form['gg_paga']
        if not gg_paga:
            gg_paga = 0
       
        if request.form['input_user_id'] == None or request.form['input_user_id'] == "":
            user_id = None
        else:
            user_id = int(request.form['input_user_id'])
        error = None

        if (not surname) or (not name) or (not type):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE people SET surname = %s, name = %s, cessato = %s, type = %s, user_id = %s, gg_paga = %s'
                ' WHERE id = %s',
                (surname, name, cessato, type, user_id, gg_paga, id)
            )
            db.commit()
            return redirect(url_for('people.index'))
    return render_template('people/update.html', people=people, userList=userList, people_types=people_types)

@bp.route('/people/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db() 
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM people_payment WHERE people_id = %s', (id,))
    cursor.execute('DELETE FROM people WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('people.index'))

@bp.route('/people/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    people = get_people(id)
    userList = get_userList()
    people_types = get_people_type()
    return render_template('people/detail.html', people=people, userList=userList, people_types=people_types)

def get_people(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, surname, name, cessato, type, user_id, gg_paga' 
        ' FROM people'
        ' WHERE id = %s',
        (id,)
    )
    people = cursor.fetchone()

    if people is None:
        abort(404, f"people id {id} non esiste.")

    return people

def get_userList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, username'
        ' FROM user ORDER BY username ASC'
    )
    userList=cursor.fetchall()

    if userList is None:
        abort(404, f"userList è vuota.")
    return userList

def get_people_type():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT name, short_name'
        ' FROM people_type ORDER BY name ASC'
    )
    people_types=cursor.fetchall()

    if people_types is None:
        abort(404, f"people_types è vuota.")
    return people_types