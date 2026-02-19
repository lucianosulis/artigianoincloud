from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime, timedelta


bp = Blueprint('order', __name__)

@bp.route('/order', methods=('GET', 'POST'))
@login_required
def index():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    
    session["activity_first_page"] = 'Y'
    session["show_calendar"] = 'N' 
    if not "order_filter" in session:
        session["order_filter"] = " WHERE order_type = 'spot' AND closed = 0"
    print(session["order_filter"])
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM p_order s INNER JOIN customer c ON s.customer_id = c.id " + session["order_filter"])
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    per_page = current_app.config["FL_PER_PAGE"]
    searchStr = " WHERE order_type = 'spot' "
    if "0" in session["order_filter"]:
        filterA = "open_only"
    else:
        filterA = "all"
    if "spot" in session["order_filter"]:    
        filterB = "spot"
    else:
        filterB = "cont"  
    
    if request.method == 'POST': 
        filterA = request.form['filterA']
        filterB = request.form['filterB']
        customer = request.form['customer']
        searchStr = ""
        if filterB == "spot":
            searchStr = " WHERE order_type = 'spot' "
        else:
            searchStr = " WHERE order_type = 'cont' "
        if filterA == "open_only":
            searchStr = searchStr + " AND closed = 0"
        if customer != "":
            searchStr = searchStr + " AND c.full_name LIKE '%" + customer.upper() + "%'"
        print(searchStr)
        current_app.logger.debug("searchStr: " + searchStr)
        session["order_filter"] = searchStr
        cursor.execute(
            'SELECT COUNT(*) AS count FROM p_order s INNER JOIN customer c ON s.customer_id = c.id ' + session["order_filter"]
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
    
    cursor.execute(
        'SELECT o.id, o.description, o.order_type, c.full_name AS customer_name, DATE_FORMAT(o.date,"%d/%m/%y") AS date'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id' + session["order_filter"] + 
        ' ORDER BY c.full_name ASC, o.date DESC LIMIT %s OFFSET %s',
        (per_page, offset)
        )
    orders = cursor.fetchall()
    return render_template('order/index.html', orders=orders, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr, filterA=filterA, filterB=filterB)

@bp.route('/order/select', methods=('GET', 'POST'))
@login_required
def select():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    
    session["activity_first_page"] = 'Y'
    if not "order_filter" in session:
        session["order_filter"] = " WHERE order_type = 'spot' AND closed = 0"
    print(session["order_filter"])
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM p_order s INNER JOIN customer c ON s.customer_id = c.id " + session["order_filter"])
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    per_page = current_app.config["FL_PER_PAGE"]
    searchStr = " WHERE order_type = 'spot' "
    if "0" in session["order_filter"]:
        filterA = "open_only"
    else:
        filterA = "all"
    if "spot" in session["order_filter"]:    
        filterB = "spot"
    else:
        filterB = "cont" 
    
    if request.method == 'POST': 
        filterA = request.form['filterA']
        filterB = request.form['filterB']
        customer = request.form['customer']
        searchStr = ""
        if filterB == "spot":
            searchStr = " WHERE order_type = 'spot' "
        else:
            searchStr = " WHERE order_type = 'cont' "
        if filterA == "open_only":
            searchStr = searchStr + " AND closed = 0"
        if customer != "":
            searchStr = searchStr + " AND c.full_name LIKE '%" + customer.upper() + "%'"
        print(searchStr)
        current_app.logger.debug("searchStr: " + searchStr)
        session["order_filter"] = searchStr
        cursor.execute(
            'SELECT COUNT(*) AS count FROM p_order s INNER JOIN customer c ON s.customer_id = c.id ' + session["order_filter"]
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
    
    #Nella seguente query elimino i doppi apici dalla colonna o.description perché altrimenti poi dà errore nel Javascript
    cursor.execute(
        'SELECT o.id, REPLACE(o.description,"""","") AS description, o.order_type, c.full_name AS customer_name, DATE_FORMAT(o.date,"%d/%m/%y") AS date'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id' + session["order_filter"] + 
        ' ORDER BY c.full_name ASC, o.date DESC LIMIT %s OFFSET %s',
        (per_page, offset)
        )
    orders = cursor.fetchall()
    return render_template('order/select.html', orders=orders, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr, filterA=filterA, filterB=filterB)


@bp.route('/order/<int:id>/close', methods=('POST',))
@login_required
def close(id):
    current_app.logger.debug("id: " + str(id))
    current_app.logger.debug("Sono nella POST del close")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE p_order SET closed = True'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    #flash("Ordine chiuso.")
    return "Closed"    #redirect(url_for('order.index'))

@bp.route('/order/<int:id>/open', methods=('POST',))
@login_required
def open(id):
    current_app.logger.debug("id: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE p_order SET closed = False'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    #flash("Ordine aperto.")
    return "Opened"  #redirect(url_for('order.index'))

@bp.route('/order/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    order = get_order(id)
    customerList = get_customerList()
    order_tags=getOrderTags(id)
    total_hours_dict = getOrderTotalHours(id)
    total_hours = total_hours_dict['total_hours']
    return render_template('order/detail.html', order=order, customerList=customerList, order_tags=order_tags, total_hours=total_hours)

@bp.route('/order/<int:id>/update_invoice_dates', methods=('GET', 'POST'))
@login_required
def update_invoice_dates(id):
    show_calendar = session["show_calendar"]
    order = get_order(id)
    customerList = get_customerList()
    total_hours_dict = getOrderTotalHours(id)
    total_hours = total_hours_dict['total_hours']
    po_invoices_arr = get_po_invoices(id)
    po_invoices = po_invoices_arr[0]
    print(po_invoices)
    
    if request.method == 'POST': 
        po_invoices_dates = request.form['po_invoices_dates']
        print("po_invoices_dates: " + po_invoices_dates)
        po_invoices_amounts = request.form['po_invoices_amounts']
        po_invoices_invoiceds = request.form['po_invoices_invoiceds']
        po_invoices_dates_arr = po_invoices_dates.split(";")
        po_invoices_proformas = request.form['po_invoices_proformas']
        po_invoices_ext_channels = request.form['po_invoices_ext_channels']
        print("lunghezza di po_invoices_dates_arr: " + str(len(po_invoices_dates_arr)))
        po_invoices_amounts_arr = po_invoices_amounts.split(";")
        po_invoices_invoiceds_arr = po_invoices_invoiceds.split(";")
        po_invoices_proformas_arr = po_invoices_proformas.split(";")
        print("date e importi dalla form:")
        print(po_invoices_dates)
        print(po_invoices_amounts)
        print("po_invoices_dates_arr:")
        print(po_invoices_dates_arr)
        #print(po_invoices_invoiceds)
        #print(po_invoices_proformas)
        po_invoices_ext_channels_arr = po_invoices_ext_channels.split(";")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('DELETE FROM po_invoices WHERE order_id = %s', (id,))
        k=0
        for po_invoices_date in po_invoices_dates_arr:
            #print("k=" + str(k))
            #print(po_invoices_date)
            
            if po_invoices_date != "":
                try:
                    #print("Data in formato non ISO?")
                    date_format = '%a %b %d %Y'
                    po_invoices_date_obj = datetime.strptime(po_invoices_date, date_format)
                    #print(po_invoices_date_obj)
                    dateISO = po_invoices_date_obj.strftime('%Y-%m-%d')
                except:
                    #print("Data già in formato ISO")
                    date_format = '%Y-%m-%d'
                    po_invoices_date_obj = datetime.strptime(po_invoices_date, date_format)
                    #print(po_invoices_date_obj)
                    dateISO = po_invoices_date_obj.strftime('%Y-%m-%d')
                
                cursor.execute('INSERT INTO po_invoices (order_id, date, amount, invoiced, proforma, ext_channel)'
                            ' VALUES (%s, %s, %s, %s, %s, %s)',
                            (id, dateISO, po_invoices_amounts_arr[k], po_invoices_invoiceds_arr[k], po_invoices_proformas_arr[k], po_invoices_ext_channels_arr[k] ))
                print("Valori scritti nel DB:")
                print(str(id) + " - " + str(dateISO) + " - " + str(po_invoices_amounts_arr[k]) + " - " + str(po_invoices_invoiceds_arr[k]) )
            
            k = k + 1
        db.commit()
        if  show_calendar == 'Y':
            return redirect(url_for('cal_order_invoice.show_cal'))
        else:
            return redirect(url_for('order.index'))
    
    return render_template('order/update_invoice_dates.html', order=order, customerList=customerList, total_hours=total_hours, po_invoices=po_invoices, show_calendar=show_calendar)

@bp.route('/order/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    #cursor.execute('SELECT COUNT(*) AS count FROM rel_tag_order WHERE p_order_id = %s', (id,))
    #rowCount = cursor.fetchone()
    #total = rowCount['count']
    #print(f"Numero tag correlati: {total}")
    cursor.execute('DELETE FROM rel_tag_order WHERE p_order_id = %s', (id,))
    db.commit()
    try:
        cursor.execute('DELETE FROM p_order WHERE id = %s', (id,))
        db.commit()
    except:
        flash("Errore nella eliminazione. Verifica che non ci siano attività programmate su questo ordine.")
    return redirect(url_for('order.index'))

@bp.route('/order/create', methods=('GET','POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("order.index"))
    customerList = get_customerList()
    anag_tags = get_anag_tags()
    if request.method == 'POST':
        title = request.form['title']
        customer_name = request.form['customer_name']
        customer_address = request.form['customer_address']
        customer_city = request.form['customer_city']
        customer_id = request.form['customer_id']
        notes = request.form['notes']
        tag_id = request.form.get('tag_id')
        print("customer_id: " + str(customer_id))
        error = None

        if ((not customer_name) or (not customer_address) or (not customer_city)) and (not customer_id):
            error = 'Scegli un cliente esistente o inserisci un nuovo cliente (nominativo, indirizzo, città).'

        if error is not None:
            flash(error)
        else:
            session["title"] = title
            session["notes"] = notes
            session['selected_tag'] = tag_id
            if customer_id != "":
                print("fc_new_order_wo_act") 
                session["fc_call_type"] = "fc_new_order_wo_act"
                session["customer_id"] = customer_id
            else:
                print("fc_new_order_new_cust")
                session["fc_call_type"] = "fc_new_order_new_cust"
                session["customer_name"] = customer_name
                session["customer_address"] = customer_address
                session["customer_city"] = customer_city
                
            return redirect('/oauth')

    return render_template('order/create.html', customerList=customerList, anag_tags=anag_tags)

@bp.route('/order/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("order.index"))
    current_app.logger.debug("id: " + str(id))
    order = get_order_w_cust(id)
    anag_tags = get_anag_tags()
    order_tags = getOrderTags(id)
    tag_ids = []
    for tag in order_tags:
        tag_ids.append(tag["tag_id"]) 
    
    if request.method == 'POST':
        current_app.logger.debug("Sono nella POST della duplicate")
        #current_app.logger.debug(request.form)
        title = request.form['title']
        date = request.form['date']
        amount = request.form['amount']
        if not amount:
            amount = 0
        notes = request.form['notes']
        customer_id = order['customer_id']
        order_type = order['order_type']
        tag_ids = request.form.getlist('tag_ids')
        error = None

        if (not title) or (not date) :
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            print("fc_new_order_duplicate")
            session["fc_call_type"] = "fc_new_order_duplicate"
            session["title"] = title
            session["customer_id"] = customer_id
            session["order_type"] = order_type
            session["order_amount"] = amount
            session["notes"] = notes 
            session["order_date"] = date
            session["old_order_id"] = id
            session["tag_ids"] = tag_ids
                
            return redirect('/oauth')

    current_app.logger.debug("Sto per fare la return da duplicate")
    return render_template('order/duplicate.html', order=order, anag_tags=anag_tags, tag_ids=tag_ids)


def get_order(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, customer_id, description, amount, DATE_FORMAT(date,"%d/%m/%y") AS date, closed, notes' 
        ' FROM p_order'
        ' WHERE id = %s',
        (id,)
    )
    order = cursor.fetchone()

    if order is None:
        abort(404, f"order id {id} non esiste.")
    
    if order['description'] == None:
        order['description'] = ""
    if order['amount'] == None:
        order['amount'] = ""
    print(order['closed'])
    return order

def get_order_w_cust(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT o.id, o.customer_id, c.full_name AS customer_fullname, o.description, o.amount, DATE_FORMAT(o.date,"%d/%m/%y") AS date, o.amount, o.order_type, notes' 
        ' FROM p_order o'
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE o.id = %s',
        (id,)
    )
    order = cursor.fetchone()

    if order is None:
        abort(404, f"order id {id} non esiste.")
    
    if order['description'] == None:
        order['description'] = ""
    if order['amount'] == None:
        order['amount'] = ""
    return order

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

def get_anag_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(id order by surname,name) AS id, GROUP_CONCAT(CONCAT(surname," ",name) order by surname,name) AS name FROM people WHERE cessato=0'
    )
    anag_people=cursor.fetchone()
    return anag_people

def getOrderTotalHours(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'select SUM(ore_lav) AS total_hours from timesheet where order_id = %s',
        (id,)
    )
    total_hours_dict=cursor.fetchone()
    return total_hours_dict

def get_po_invoices(id):
    current_app.logger.debug("get_po_invoices")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'SELECT GROUP_CONCAT(date SEPARATOR ";") AS date, GROUP_CONCAT(amount SEPARATOR ";") AS amount, ' 
       ' GROUP_CONCAT(invoiced SEPARATOR ";") AS invoiced,'
       ' GROUP_CONCAT(proforma SEPARATOR ";") AS proforma,'
       ' GROUP_CONCAT(ext_channel SEPARATOR ";") AS ext_channel'
       ' FROM po_invoices WHERE order_id = %s', (id,)
    )
    po_invoices=cursor.fetchone()
    return [po_invoices] 

def getOrderTags(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT t.id AS tag_id, CONCAT(t.code," - ",t.description) AS tag_desc'
        ' FROM tag t' 
        ' INNER JOIN rel_tag_order rto ON rto.tag_id=t.id '
        ' WHERE rto.p_order_id=%s'
        ' ORDER BY t.code ASC',(order_id,)
    )
    order_tags=cursor.fetchall()
    if order_tags is None:
        abort(404, f"order_tags è vuota.")
    return order_tags

def get_anag_tags():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tag_id, CONCAT(code," - ",description) AS tag_desc'
        ' FROM tag'
        ' ORDER BY code ASC'
    )
    tags=cursor.fetchall()

    if tags is None:
        abort(404, f"tags è vuota.")
    return tags