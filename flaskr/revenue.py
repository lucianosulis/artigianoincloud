from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    url_for, current_app, jsonify, json, session, 
    send_from_directory)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date
from datetime import datetime

bp = Blueprint('revenue', __name__)

@bp.route('/revenue', methods=('GET', 'POST'))
@login_required
def index():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("home.index"))
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    db = get_db() 
    cursor = db.cursor(dictionary=True)
    #Creazione filtro
    current_year = date.today().year
    active_year = session.get("active_year",current_year)
    conditions = []
    params = []
    conditions.append("year = %s")
    params.append(f"{active_year}")
    searchStr = " WHERE " + " AND ".join(conditions)
    
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        conditions2 = session.get("rev_search_conditions2", [])
        params2 = session.get("rev_search_conditions2_search_params2", [])
        search_date = session.get("rev_search_date","")
        search_customer = session.get("rev_search_customer","")
        search_order = session.get("rev_search_order","")
        if conditions2:
            searchStr = searchStr + " AND " + " AND ".join(conditions2)
            params = params + params2
    
    if request.method == 'POST': 
        page = 1
        search_date = request.form.get("searchDate","")
        search_customer = request.form.get("searchCustomer","")
        search_order = request.form.get("searchSite","")
        session["rev_search_date"] = search_date
        session["rev_search_customer"] = search_customer
        session["rev_search_order"] = search_order
        # 1. Inizializziamo una lista per le condizioni aggiuntive e una per i parametri
        conditions2 = []
        params2 = []
        if search_date:
            conditions2.append("r.date = %s")
            params2.append(f"{search_date}") 
        if search_customer:
            conditions2.append("full_name LIKE %s")
            params2.append(f"%{search_customer}%") # Il % lo mettiamo nel dato, non nella query
        if search_order:
            conditions2.append("o.description LIKE %s")
            params2.append(f"%{search_order}%") # Il % lo mettiamo nel dato, non nella query
       
        # 2. Trasformiamo la lista di condizioni in una stringa da aggiungere alla clausola WHERE
        if conditions2:
            searchStr = searchStr + " AND " + " AND ".join(conditions2)
            params = params + params2
            
        session["rev_search_conditions2"] = conditions2
        session["rev_search_params2"] = params2

    count_query = ('''SELECT COUNT(*) AS count FROM 
                 (SELECT r.id, r.number, r.date, r.object, r.amount_net, r.comp_start, r.comp_end, c.full_name AS customer,
                 o.description AS order_desc, o.order_type AS order_type
                 FROM revenue r
                 LEFT JOIN p_order o ON r.order_id = o.id
			     LEFT JOIN customer c ON r.customer_id = c.id ''' +
                searchStr + ") AS revenues"
                )
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    offset = (page-1) * per_page 
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')

    final_query = ('''SELECT r.id, r.number, DATE_FORMAT(r.date,"%d/%m/%y") AS date, r.object, r.amount_net, DATE_FORMAT(r.comp_start,"%d/%m/%y"), DATE_FORMAT(r.comp_end,"%d/%m/%y"), c.full_name AS customer,
                 o.description AS order_desc, o.order_type AS order_type
                 FROM revenue r
                 LEFT JOIN p_order o ON r.order_id = o.id
			     LEFT JOIN customer c ON r.customer_id = c.id''' +
             searchStr +
            ' ORDER BY r.date ASC LIMIT %s OFFSET %s'
        )
    # Aggiungiamo LIMIT e OFFSET alla lista dei parametri esistenti
    final_params = params + [per_page, offset]
    print(f"final_query: {final_query}")
    print(final_params)
    cursor.execute(final_query, final_params)
    revenues = cursor.fetchall() 
    
    return render_template('revenue/index.html', revenues=revenues,pagination=pagination,search_date=search_date,search_customer=search_customer,search_order=search_order)

@bp.route('/revenue/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("revenue.index"))
    redirect_url = url_for('revenue.index')
    revenue = get_revenue(id)
    #print(f"revenue id: {id}")
    customer_id = revenue['customer_id']
    order_list = get_order_list(customer_id)

    #order_id = act['p_order_id']
    #order_desc = get_order(id)

    if request.method == 'POST': 
        comp_start = request.form.get('comp_start')
        comp_end = request.form.get('comp_end')
        order_id = request.form.get('order_id')

        error = None

        if (not comp_start) or (not comp_end) or (not order_id):
            error = 'Compila tutti i campi obbligatori.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE revenue SET comp_start = %s, comp_end = %s, order_id = %s '
                ' WHERE id = %s',
                (comp_start, comp_end, order_id, id)
            )
            db.commit() 
            return redirect(redirect_url)
    return render_template('revenue/update.html', revenue=revenue, order_list=order_list, redirect_url=redirect_url)

@bp.route('/revenue/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(redirect_url)
    redirect_url = url_for('revenue.index')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM revenue WHERE id = %s', (id,))
    db.commit()
    return redirect(redirect_url)

@bp.route('/revenue/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("revenue.index"))
    redirect_url = url_for('revenue.index')
    revenue = get_revenue(id)
    customer_id = revenue['customer_id']
    order_list = get_order_list(customer_id)
    return render_template('revenue/detail.html', revenue=revenue, order_list=order_list, redirect_url=redirect_url)

@bp.route("/<int:order_id>/order_desc", methods=('POST',))
@login_required
def order_desc(order_id):
    #current_app.logger.debug("order_desc dice: " + str(order_id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT description FROM p_order WHERE id = %s', (order_id,))
    row = cursor.fetchone()
    order_desc = row['description']
    result= order_desc
    return (result)

def get_revenue(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        '''SELECT r.id, r.object, r.number, r.date, r.order_id, o.description AS order_desc,
        r.customer_id,r.customer_name, r.amount_net,r.type,
        r.comp_start, r.comp_end
        FROM revenue r 
        LEFT JOIN p_order o ON r.order_id = o.id 
        WHERE r.id = %s''',
        (id,)
    )
    revenue = cursor.fetchone()
    current_app.logger.debug(revenue)
    if revenue is None:
        abort(404, f"revenue id {id} non esiste.")

    return revenue

def get_orderList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT o.id, o.description, c.full_name'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE o.closed=0'
        ' ORDER BY c.full_name ASC'
    )
    orderList=cursor.fetchall()

    if orderList is None:
        abort(404, f"orderList è vuota.")
    return orderList

def get_customerList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT c.id, c.full_name, c.address, c.city'
        ' FROM customer c'
        ' ORDER BY c.full_name ASC'
    )
    customerList=cursor.fetchall()

    if customerList is None:
        abort(404, f"customerList è vuota.")
    return customerList

def get_order(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        ' SELECT CONCAT(c.full_name," - ",o.description," - ",DATE_FORMAT(o.date,"%d/%m/%Y") ) AS order_desc'
        ' FROM activity a '
        ' INNER JOIN p_order o ON a.p_order_id = o.id'
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE a.id = %s', (id,)
    )
    order=cursor.fetchone()
    return order

def get_order_desc(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        ' SELECT CONCAT(c.full_name," - ",o.description," - ",DATE_FORMAT(o.date,"%d/%m/%Y") ) AS order_desc'
        ' FROM p_order o '
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE o.id = %s', (id,)
    )
    order=cursor.fetchone()
    return order

def get_siteList(order_id):
    #current_app.logger.debug("get_siteList")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id, s.address, s.city, c.full_name'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id'
        ' INNER JOIN site s ON c.id = s.customer_id'
        ' WHERE o.id = %s',
        (order_id,)
        )
    siteList=cursor.fetchall()
    if siteList is None:
        abort(404, f"siteList è vuota.")
    #current_app.logger.debug(siteList)
    return siteList

def get_siteList2(customer_id):
    #current_app.logger.debug("get_siteList2")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id, s.address, s.city, c.full_name'
        ' FROM customer c '
        ' INNER JOIN site s ON c.id = s.customer_id'
        ' WHERE c.id = %s',
        (customer_id,)
        )
    siteList=cursor.fetchall()

    if siteList is None:
        abort(404, f"siteList è vuota.")
    #current_app.logger.debug(siteList)
    return siteList

def get_order_list(customer_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        '''SELECT id, description, date 
         FROM p_order 
         WHERE customer_id = %s
         ORDER BY date DESC''',
        (customer_id,)
    )
    order_list=cursor.fetchall()
    return order_list

