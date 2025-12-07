from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('site', __name__)

@bp.route('/site', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM site')
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
            'SELECT COUNT(*) AS count FROM site s INNER JOIN customer c ON s.customer_id = c.id WHERE c.full_name LIKE %s',
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
            'SELECT s.id, s.address AS address, s.city AS city, c.full_name AS customer_name'
            ' FROM site s INNER JOIN customer c ON s.customer_id = c.id'
            ' ORDER BY c.full_name ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
        sites = cursor.fetchall()
    else:
        searchQ = "%" + searchStr + "%"
        searchQ = searchQ.upper()
        cursor.execute(
            'SELECT s.id, s.address AS address, s.city AS city, c.full_name AS customer_name'
            ' FROM site s INNER JOIN customer c ON s.customer_id = c.id'
            ' WHERE c.full_name LIKE %s'
            ' ORDER BY c.full_name ASC LIMIT %s OFFSET %s',
            (searchQ, per_page, offset)
        )
        sites = cursor.fetchall()
    return render_template('site/index.html', sites=sites, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/site/create', methods=('GET', 'POST'))
@login_required
def create():
    customerList = get_customerList()
    if request.method == 'POST':
        customer_id = request.form['input_customer_id']
        city = request.form['city']
        address = request.form['address']
        contact_people = request.form['contact_people']
        telephone = request.form['telephone']
        email = request.form['email']
        error = None

        if (not customer_id) or (not city) or (not address):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO site (customer_id, city, address, contact_people, telephone, email)'
                ' VALUES (%s, %s, %s, %s, %s, %s)',
                (customer_id, city, address, contact_people, telephone, email)
            )
            db.commit()
            return redirect(url_for('site.index'))

    return render_template('site/create.html', customerList=customerList)

@bp.route('/site/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    current_app.logger.debug("id: " + str(id))
    site = get_site(id)
    customerList = get_customerList()
    customer_id = site['customer_id']
    
    if request.method == 'POST':
        current_app.logger.debug("Sono nella POST del update")
        customer_id = request.form['input_customer_id']
        city = request.form['city']
        address = request.form['address']
        contact_people = request.form['contact_people']
        telephone = request.form['telephone']
        email = request.form['email']
        error = None

        if (not customer_id) or (not city) or (not address):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE site SET customer_id = %s, city = %s, address = %s, contact_people = %s, telephone = %s, email = %s'
                ' WHERE id = %s',
                (customer_id, city, address, contact_people, telephone, email, id)
            )
            db.commit()
            return redirect(url_for('site.index'))
    current_app.logger.debug("Sto per fare la return da update")
    return render_template('site/update.html', site=site, customerList=customerList)

@bp.route('/site/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM site WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('site.index'))

@bp.route('/site/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    site = get_site(id)
    customerList = get_customerList()
    return render_template('site/detail.html', site=site, customerList=customerList)

def get_site(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, customer_id, address, city, contact_people, telephone, email' 
        ' FROM site'
        ' WHERE id = %s',
        (id,)
    )
    site = cursor.fetchone()

    if site is None:
        abort(404, f"site id {id} non esiste.")
    
    if site['contact_people'] == None:
        site['contact_people'] = ""
    if site['telephone'] == None:
        site['telephone'] = ""
    if site['email'] == None:
        site['email'] = ""

    return site

def get_customerList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, full_name, city'
        ' FROM customer ORDER BY full_name ASC'
    )
    customerList=cursor.fetchall()

    if customerList is None:
        abort(404, f"customerList è vuota.")
    return customerList
