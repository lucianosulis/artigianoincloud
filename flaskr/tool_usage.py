from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime, timedelta
from dateutil.easter import *

bp = Blueprint('tool_usage', __name__)

@bp.route('/tool_usage', methods=('GET', 'POST'))
@login_required
def index():
    
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    
    session["activity_first_page"] = 'Y'
    session["show_calendar"] = 'N'
   
    if not "search" in session:
        session["search"] = " "
    searchStr = session["search"]
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    current_app.logger.debug("searchStr 1: " + searchStr)
    current_app.logger.debug("session.get('search'): " + str(session.get('search')))
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT tu.id, tu.date as date, tt.type as tool_type, CONCAT(t.brand," ",t.model) as t_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, tu.ore_lav'
            ' FROM tool_usage tu' 
            ' LEFT JOIN p_order o on tu.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN tool t on tu.tool_id = t.id '
            ' INNER JOIN tool_type tt on t.tool_type_id = tt.id ' +
            searchStr + ") AS tu_tables" 
            )
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]

    if request.method == 'POST': 
        page = "1"
        searchDate = request.form['searchDate']
        searchCustomer = request.form['searchCustomer']
        searchTool = request.form['searchTool']
        if ((searchDate + searchCustomer + searchTool) != "") and searchStr == "":
            searchStr = " WHERE "
        if (searchDate != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + "tu.date = '" + searchDate + "'"
        if (searchCustomer != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " c.full_name LIKE '%" + searchCustomer + "%'"
        if (searchTool != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " CONCAT(t.brand,\" \",t.model) LIKE '%" + searchTool + "%'"
        #searchStr = searchStr.upper()
        current_app.logger.debug("searchStr 2: " + searchStr)
        session["search"] = searchStr
        current_app.logger.debug("session.search: " + session["search"])
        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT tu.id, tu.date as date, tt.type as tool_type, CONCAT(t.brand," ",t.model) as t_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, tu.ore_lav'
            ' FROM tool_usage tu' 
            ' LEFT JOIN p_order o on tu.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN tool t on tu.tool_id = t.id '
            ' INNER JOIN tool_type tt on t.tool_type_id = tt.id ' +
            searchStr + ") AS tu_tables"  
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
        #print("total=" + str(total))
    if page != None:
        offset = (int(page)-1) * per_page
    else:
        page = "1"
        offset = 0   
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    #print(str(per_page) + " ----- " + str(offset))
    cursor.execute(
            ' SELECT tu.id, tu.date as date, tt.type as tool_type, CONCAT(t.brand," ",t.model) as t_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, tu.ore_lav'
            ' FROM tool_usage tu' 
            ' LEFT JOIN p_order o on tu.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN tool t on tu.tool_id = t.id '
            ' INNER JOIN tool_type tt on t.tool_type_id = tt.id ' + 
            str(searchStr) +
            ' ORDER BY tu.date DESC, t_name ASC LIMIT %s OFFSET %s', 
            (per_page, offset)
        )
    tu_records = cursor.fetchall()
    
    return render_template('tool_usage/index.html', tu_records=tu_records, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/tool_usage/create', methods=('GET', 'POST'))
@login_required
def create():
    anag_tool = get_anag_tool()
    date = datetime.today().strftime('%Y-%m-%d')
    orders = get_orderListFiltered2(date)
    order_ids = orders["order_id"]
    order_descs = orders["order_desc"]
    if order_ids == None:
        order_ids = ""
        order_descs = ""
    #Aggiungo un elemento vuoto per la jsgrid dell'interfaccia utente
    order_ids = "," + order_ids 
    order_descs = "|§|" + order_descs
    orders = {"order_id" : order_ids, "order_desc" : order_descs}

    if request.method == 'POST':
        date = request.form['date']
        tool_ids = request.form['input_tool_ids']
        
        error = None

        if (not date) or (not tool_ids):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            order_ids_sel = request.form['order_ids_sel']
            ore_lavs_sel = request.form['ore_lavs_sel']
            order_ids_sel_arr = order_ids_sel.split(",")
            ore_lavs_sel_arr = ore_lavs_sel.split(",")

            db = get_db()
            tool_ids_arr = tool_ids.split(",") 
            for tool_id in tool_ids_arr:
                k=0
                while k < len(order_ids_sel_arr):
                    
                    if order_ids_sel_arr[k] != "":
                        order_id = int(order_ids_sel_arr[k])
                    else:
                        order_id = None
                    if ore_lavs_sel_arr[k] != "":
                        ore_lav = float(ore_lavs_sel_arr[k])
                    else:
                        ore_lav = 0
                    
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO tool_usage (date, tool_id, order_id, ore_lav)'
                        ' VALUES (%s, %s, %s, %s)',
                        (date, tool_id, order_id, ore_lav)
                    )
                    k = k + 1
            db.commit()
            return redirect(url_for('tool_usage.index'))

    return render_template('tool_usage/create.html', orders=orders, anag_tool=anag_tool)

@bp.route('/tool_usage/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    current_app.logger.debug("id: " + str(id))
    tu_record = get_tu_record(id)
    anag_tool = get_anag_tool()
    date = tu_record['date']
    #orderList = get_orderList() #Non filtrata
    orderList = get_orderListFiltered(date)

    if request.method == 'POST':
        date = request.form['date']
        tool_id = request.form['input_tool_id']
        order_id = request.form['input_order_id']
        ore_lav = request.form['ore_lav']
        
        error = None
        print("Debug:")
        print(date)
        print(tool_id)
        print(ore_lav)
        print(order_id)

        if (not date)  or (not tool_id) or (not order_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
               'UPDATE tool_usage SET date = %s, tool_id = %s, order_id = %s, ore_lav = %s'
                ' WHERE id = %s',
                (date, tool_id, order_id, ore_lav, id)
            )
            db.commit()
            return redirect(url_for('tool_usage.index'))
    return render_template('tool_usage/update.html', tu_record=tu_record, orderList=orderList, anag_tool=anag_tool)

@bp.route('/tool_usage/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    current_app.logger.debug("id: " + str(id))
    tu_record = get_tu_record(id)
    anag_tool = get_anag_tool()
    #orderList = get_orderList()
    date = tu_record['date']
    orderList = get_orderListFiltered(date)

    if request.method == 'POST':
        date = request.form['date']
        tool_id = request.form['input_tool_id']
        order_id = request.form['input_order_id']
        ore_lav = request.form['ore_lav']
        
        error = None

        if (not date)  or (not tool_id) or (not order_id):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO tool_usage (date, tool_id, order_id, ore_lav)'
                ' VALUES (%s, %s, %s, %s)',
                (date, tool_id, order_id, ore_lav)
            )
            db.commit()
            return redirect(url_for('tool_usage.index'))
    return render_template('tool_usage/update.html', tu_record=tu_record, orderList=orderList, anag_tool=anag_tool)


@bp.route('/tool_usage/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM tool_usage WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('tool_usage.index'))


@bp.route('/tool_usage/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    tu_record = get_tu_record(id)
    orderList = get_orderList()
    anag_tool = get_anag_tool()
    return render_template('tool_usage/detail.html', tu_record=tu_record, orderList=orderList, anag_tool=anag_tool, show_calendar = session["show_calendar"])

@bp.route("/tu_sel_order/<date>", methods=('POST',))
@login_required
def sel_order(date):
    orderList = get_orderListFiltered(date)
    return (orderList)

@bp.route("/tu_sel_order2/<date>", methods=('POST',))
@login_required
def sel_order2(date):
    orders = get_orderListFiltered2(date)
    order_ids = orders["order_id"]
    order_descs = orders["order_desc"]
    #Aggiungo un elemento vuoto per la jsgrid dell'interfaccia utente
    order_ids = "," + order_ids 
    order_descs = "|§|" + order_descs
    orderList = {"order_id" : order_ids, "order_desc" : order_descs}
    return (orderList)

def get_tu_record(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, date, tool_id, order_id, ore_lav' 
        ' FROM tool_usage '
        ' WHERE id = %s',
        (id,)
    )
    tu_record = cursor.fetchone()
    if tu_record is None:
        abort(404, f"tu_record id {id} non esiste.")

    return tu_record

def get_orderList():
    #Con questa query si ottengono tutti gli ordini
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT o.id, o.description, c.full_name'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id'
        ' ORDER BY c.full_name ASC'
    )
    orderList=cursor.fetchall()
    
    if orderList is None:
        abort(404, f"orderList è vuota.")
    return orderList

def get_orderListFiltered(date):
    #Con questa query si ottengono solo gli ordini che hanno almeno un'attività 
    # programmata nel giorno in cui si consuntiva (date)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT DISTINCT o.id, o.description, c.full_name'
        ' FROM p_order o '
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' INNER JOIN activity a ON o.id = a.p_order_id '
        ' WHERE %s >= a.start AND %s <= a.end '
        ' ORDER BY c.full_name ASC',
        (date,date)
    )
    orderList = cursor.fetchall()

    if orderList is None:
        abort(404, f"orderList è vuota.")
    return orderList

def get_orderListFiltered2(date):
    #Con questa query si ottengono solo gli ordini che hanno almeno un'attività 
    # programmata nel giorno in cui si consuntiva (date) ma resi come unico record
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(o.id) AS order_id, GROUP_CONCAT(CONCAT(c.full_name, " - ", o.description) SEPARATOR "|§|") AS order_desc'
        ' FROM p_order o '
        ' INNER JOIN customer c ON o.customer_id = c.id '
        ' INNER JOIN activity a ON o.id = a.p_order_id '
        ' WHERE %s >= a.start AND %s <= a.end '
        ' ORDER BY c.full_name ASC',
        (date,date)
    )
    orders = cursor.fetchone()
    if orders is None:
        abort(404, f"orders è vuota.")
    return orders

def get_anag_tool():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(brand," ",model) AS t_name FROM tool' 
        ' WHERE discontinued=0 ORDER BY brand,model ASC'
    )
    anag_tool=cursor.fetchall()
    return anag_tool

def get_anag_tool2():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(id order by brand,model) AS id, GROUP_CONCAT(CONCAT(brand," ",model) order by brand,model) AS t_name FROM tool '
        ' WHERE discontinued=0'
    )
    anag_tool=cursor.fetchone()
    return anag_tool
