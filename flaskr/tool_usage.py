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
   
    if not "search" in session:
        session["search"] = ""
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
        #print("searchDate + searchCustomer + searchTool: " + searchDate + searchCustomer + searchTool)
        if ((searchDate + searchCustomer + searchTool) != "") and searchStr == "":
            searchStr = " WHERE "
            #print("searchStr con WHERE?: " + searchStr)
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
        if (searchDate + searchCustomer + searchTool) == "":
            searchStr = ""
            session["search"] = searchStr
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
            ' SELECT tu.id, tu.date as date, tt.type as tool_type, CONCAT(t.brand," ",t.model) as t_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, tu.ore_lav, tu.km'
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
    ld_anag_tools = get_anag_tools()
    anag_tools = json.dumps(ld_anag_tools) #json
    date = datetime.today().strftime('%Y-%m-%d')
    acts_ld = get_actsFiltered(date) #lista dizionari
    acts_ld.insert(0, {'act_desc': '','act_id': 0,'p_order_id': 0 })
    acts = json.dumps(acts_ld) #json

    if request.method == 'POST':
        date = request.form['date']
        dati_json_stringa = request.form.get('dati_griglia_json')
        #print(dati_json_stringa)
        dati_griglia = []
        if dati_json_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia = json.loads(dati_json_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'
        error = None

        if (not date):
            error = 'Compila tutti i campi obbligatori.'
        if (not dati_griglia):
            error = 'Devi inserire almeno un utilizzo mezzo.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            for record in dati_griglia:
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                act_id = record['act_id']
                cursor.execute('SELECT p_order_id FROM activity ' 
                    ' WHERE id=%s', (act_id,))
                result = cursor.fetchone()
                order_id = result['p_order_id']
                ore_lav = record['ore_lav']  
                km = record['km']      
                tool_id = record['tool_id']
                cursor.execute(
                    'INSERT INTO tool_usage (date, tool_id, act_id, order_id, ore_lav, km) '
                    ' VALUES (%s, %s, %s, %s, %s, %s)',
                    (date, tool_id, act_id, order_id, ore_lav, km)
                )
            db.commit()
            return redirect(url_for('tool_usage.index'))

    return render_template('tool_usage/create.html', acts=acts, anag_tools=anag_tools)

@bp.route('/tool_usage/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    tu_record = get_tu_record(id)
    anag_tools = get_anag_tools()
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari

    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        date = request.form.get('date')
        tool_id = request.form.get('tool_id')
        act_id = request.form.get('act_id')
        ore_lav = request.form['ore_lav']
        if ore_lav == "":
            ore_lav = None
        km = request.form['km']
        if km == "":
            km = None
        
        error = None

        if (not date)  or (not tool_id) or (not act_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            cursor.execute('SELECT p_order_id FROM activity ' 
                ' WHERE id=%s', (act_id,))
            result = cursor.fetchone()
            order_id = result['p_order_id']
            cursor.execute(
               'UPDATE tool_usage SET date = %s, tool_id = %s, act_id = %s, order_id = %s, ore_lav = %s, km = %s '
                ' WHERE id = %s',
                (date, tool_id, act_id, order_id, ore_lav, km, id)
            )
            db.commit()
            return redirect(url_for('tool_usage.index'))
    return render_template('tool_usage/update.html', tu_record=tu_record, acts=acts, anag_tools=anag_tools)

@bp.route('/tool_usage/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    tu_record = get_tu_record(id)
    anag_tools = get_anag_tools()
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari

    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        date = request.form.get('date')
        tool_id = request.form.get('tool_id')
        act_id = request.form.get('act_id')
        ore_lav = request.form['ore_lav']
        if ore_lav == "":
            ore_lav = 0
        km = request.form['km']
        if km == "":
            km = 0
        cursor.execute('SELECT p_order_id FROM activity ' 
                    ' WHERE id=%s', (act_id,))
        result = cursor.fetchone()
        order_id = result['p_order_id']
                
        error = None

        if (not date)  or (not tool_id) or (not act_id):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            cursor.execute(
                    'INSERT INTO tool_usage (date, tool_id, act_id, order_id, ore_lav, km) '
                    ' VALUES (%s, %s, %s, %s, %s, %s)',
                    (date, tool_id, act_id, order_id, ore_lav, km)
                )
            db.commit()
            return redirect(url_for('tool_usage.index'))
    return render_template('tool_usage/update.html', tu_record=tu_record, acts=acts, anag_tools=anag_tools)


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
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari
    anag_tools = get_anag_tools()
    return render_template('tool_usage/detail.html', tu_record=tu_record, acts=acts, anag_tools=anag_tools)

@bp.route("/tu_sel_act/<date>", methods=('POST',))
@login_required
def sel_act(date):
    acts = get_actsFiltered(date)
    return (acts)

@bp.route("/tu_sel_act2/<date>", methods=('POST',))
@login_required
def sel_act2(date):
    acts_ld = get_actsFiltered(date)
    #Aggiungo un elemento vuoto per la jsgrid dell'interfaccia utente
    acts_ld.insert(0, {'act_desc': '','act_id': 0,'p_order_id': 0 })
    acts = json.dumps(acts_ld) #json
    return (acts)

def get_tu_record(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, date, tool_id, act_id, order_id, ore_lav, km ' 
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

def get_anag_tools():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tool_id, CONCAT(brand," ",model, " ", license_plate) AS tool_name ' 
        ' FROM tool WHERE discontinued=0 ORDER BY brand,model ASC'
    )
    anag_tools=cursor.fetchall()
    return anag_tools

def get_actsFiltered(date):
    # Con questa query si ottengono solo le attività  
    # programmate nel giorno in cui si consuntiva (date)
    # viene estratto anche l'ID dell'ordine
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT a.id AS act_id, CONCAT(c.full_name, " - ", a.title) AS act_desc, ' \
        ' o.id as p_order_id'
        ' FROM p_order o '
        ' INNER JOIN customer c ON o.customer_id = c.id '
        ' INNER JOIN activity a ON o.id = a.p_order_id '
        ' WHERE %s >= a.start AND %s <= a.end '
        ' ORDER BY c.full_name ASC',
        (date,date)
    )
    acts = cursor.fetchall()
    if acts is None:
        abort(404, f"acts è vuota.")
    return acts
