from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('customer', __name__)

@bp.route('/customer', methods=('GET', 'POST'))
@login_required
def index():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("home.index"))
    customers,pagination = select_customer()
    return render_template('customer/index.html', customers=customers,pagination=pagination)

@bp.route('/customer/select', methods=('GET', 'POST'))
@login_required
def select():
    customers,pagination = select_customer()
    return render_template('customer/select.html', customers=customers,pagination=pagination)

@bp.route('/customer/select_wo_site', methods=('GET', 'POST'))
@login_required
def select_wo_site():
    customers,pagination = select_customer()
    return render_template('customer/select_wo_site.html', customers=customers,pagination=pagination)

@bp.route('/customer/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    customer = get_customer(id)
    return render_template('customer/detail.html', customer=customer)

@bp.route('/customer/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("customer.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('DELETE FROM customer WHERE id = %s', (id,))
        db.commit()
    except:
        flash("Errore nella eliminazione del cliente. Verifica che non ci siano ordini o attività programmate per questo cliente.")
    return redirect(url_for('customer.index'))

def get_customer(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, full_name, city, address, zip_code' 
        ' FROM customer'
        ' WHERE id = %s',
        (id,)
    )
    customer = cursor.fetchone()

    if customer is None:
        abort(404, f"customer id {id} non esiste.")
    
    if customer['fulll_name'] == None:
        customer['city'] = ""
    if customer['address'] == None:
        customer['zip_code'] = ""
    return customer

def select_customer():
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]

    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        params = session.get("cu1_search_params", [])
        searchStr = session.get("cu1_search","")

    if request.method == 'POST': 
        page = 1
        customer_filter = request.form.get("customer","")
        session["cu1_customer_filter"] = customer_filter
        # 1. Inizializziamo una lista per le condizioni e una per i parametri
        conditions = []
        params = []
        if customer_filter:
            conditions.append("full_name LIKE %s")
            params.append(f"%{customer_filter}%") # Il % lo mettiamo nel dato, non nella query
        # 2. Trasformiamo la lista di condizioni in una stringa WHERE
        searchStr = ""
        if conditions:
            searchStr = " WHERE " + " AND ".join(conditions)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    count_query = (
        'SELECT COUNT(*) AS count FROM customer ' + searchStr
        )
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    offset = (page-1) * per_page 
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')

    final_query = (
        'SELECT id, full_name AS customer_name, city, address'
        ' FROM customer ' + searchStr + 
        ' ORDER BY full_name ASC LIMIT %s OFFSET %s'
        )
    # Aggiungiamo LIMIT e OFFSET alla lista dei parametri esistenti
    final_params = params + [per_page, offset]
    cursor.execute(final_query, final_params)
    customers = cursor.fetchall()
    return customers,pagination