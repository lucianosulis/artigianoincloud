from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('people_payment', __name__)

@bp.route('/people_payment', methods=('GET',))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM people_payment pp' 
                   ' INNER JOIN people p ON pp.people_id=p.id'
                   ' WHERE p.cessato=0')
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    page = request.args.get('page')
    if not page:
        page = 1
        offset = 0 
    else:
        offset = (int(page)-1) * per_page  
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    
    cursor.execute(
        'SELECT pp.id AS id, CONCAT(p.surname, " ", p.name) AS people_name, p.type, CASE WHEN pp.payment_date IS NULL THEN "---" ELSE DATE_FORMAT(pp.payment_date,"%d/%m/%y") END  AS payment_date'
        ' FROM people_payment pp INNER JOIN people p ON pp.people_id=p.id'
        ' WHERE p.cessato=0'
        ' ORDER BY people_name ASC LIMIT %s OFFSET %s',
        (per_page, offset)
        )
    people_payments = cursor.fetchall()

    return render_template('people_payment/index.html', people_payments=people_payments, page=page,
                           per_page=per_page,pagination=pagination)

@bp.route('/people_payment/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    people_payment = get_people_payment(id)
    people_types = get_people_type()
    
    if request.method == 'POST':
        payment_date = request.form['payment_date']
        notes = request.form['notes']
        
        error = None

        if (not payment_date):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE people_payment SET payment_date = %s, notes = %s'
                ' WHERE id = %s',
                (payment_date, notes, id)
            )
            db.commit()
            return redirect(url_for('people_payment.index'))
    return render_template('people_payment/update.html', people_payment=people_payment, people_types=people_types)

def get_people_payment(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT pp.id AS id, p.surname, p.name, p.type, pp.payment_date, IF(pp.notes IS NULL, "", pp.notes) AS notes '
        ' FROM people_payment pp INNER JOIN people p ON pp.people_id=p.id'
        ' WHERE pp.id = %s',
        (id,)
    )
    people = cursor.fetchone()

    if people is None:
        abort(404, f"people_payment id {id} non esiste.")

    return people

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