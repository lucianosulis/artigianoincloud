from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime, timedelta

bp = Blueprint('accounting_hours', __name__)

@bp.route('/accounting_hours', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y' 
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM people WHERE user_id=%s',(g.user_id,))
    rowCount = cursor.fetchone()
    total = rowCount['count']
    if total == 0:
        flash("Questo utente non è in anagrafica del personale.")
        return redirect(url_for('home.index'))
    cursor.execute('SELECT COUNT(*) AS count FROM timesheet ts'
                   ' INNER JOIN people p ON ts.people_id = p.id' 
                   ' WHERE p.user_id=%s AND ts.locked=False',(g.user_id,)) 
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 
        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT ts.id, ts.date as date, at.description as act_type, CONCAT(p.surname," ",p.name) as p_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, ts.ore_lav'
            ' FROM timesheet ts' 
            ' LEFT JOIN p_order o on ts.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN act_type at on ts.act_type_id = at.id'
            ' INNER JOIN people p on ts.people_id = p.id ' 
            #' WHERE p.user_id = %s AND ts.locked=False'
            ' WHERE p.user_id = %s '
            ') AS ts_tables', 
            (g.user_id,)
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
            ' SELECT ts.id, ts.date as date, at.description as act_type, CONCAT(p.surname," ",p.name) as p_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, ts.ore_lav'
            ' FROM timesheet ts' 
            ' LEFT JOIN p_order o on ts.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN act_type at on ts.act_type_id = at.id'
            ' INNER JOIN people p on ts.people_id = p.id ' +
            #' WHERE p.user_id = %s AND ts.locked=False'
            ' WHERE p.user_id = %s '
            ' ORDER BY ts.date DESC LIMIT %s OFFSET %s', 
            (g.user_id, per_page, offset)
        )
    ts_records = cursor.fetchall()
    
    return render_template('accounting_hours/index.html', ts_records=ts_records, page=page,
                           per_page=per_page,pagination=pagination)

@bp.route('/accounting_hours/create', methods=('GET', 'POST'))
@login_required
def create():
    people = get_people() 
    act_types_ld = get_act_type_List() #lista dizionari
    act_types = json.dumps(act_types_ld) #json
    date = datetime.today().strftime('%Y-%m-%d')
    acts_ld = get_actsFiltered(date) #lista dizionari
    acts_ld.insert(0, {'act_desc': '','act_id': 0,'p_order_id': 0 })
    acts = json.dumps(acts_ld) #json
    ld_anag_tools1 = get_anag_tools_ore()
    anag_tools1 = json.dumps(ld_anag_tools1) #json

    if request.method == 'POST': 
        date = request.form['date']
        people_id = request.form['input_people_id']
        error = None
        dati_json_stringa = request.form.get('dati_griglia_json')
        dati_griglia = []
        if dati_json_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia = json.loads(dati_json_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'
        dati_json_stringa1 = request.form.get('dati_griglia_json1')
        #print(dati_json_stringa1)
        dati_griglia1 = []
        if dati_json_stringa1:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia1 = json.loads(dati_json_stringa1)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia 1")
                error = 'Errore nella decodifica dei dati JSON della griglia 1.'
        
        if (not date):
            error = 'Compila tutti i campi obbligatori.'
        if (not dati_griglia):
            error = 'Devi inserire almeno una presenza.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            for record in dati_griglia:
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                act_type_id = record['act_type_id']
                if act_type_id != 1:
                    act_id = None
                    order_id = None
                else:
                    act_id = record['act_id']
                    cursor.execute('SELECT p_order_id FROM activity ' 
                        ' WHERE id=%s', (act_id,))
                    result = cursor.fetchone()
                    order_id = result['p_order_id']
                
                ore_lav = record['ore_lav']
                night = record['night']
                cursor.execute(
                        'INSERT INTO timesheet (date, act_type_id, people_id, order_id, ore_lav, night, act_id)'
                        ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (date, act_type_id, people_id, order_id, ore_lav, night, act_id)
                    )
                
            for record in dati_griglia1:
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                act_id = record['act_id']
                cursor.execute('SELECT p_order_id FROM activity ' 
                    ' WHERE id=%s', (act_id,))
                result = cursor.fetchone()
                order_id = result['p_order_id']
                ore_lav = record['ore_lav']        
                tool_id = record['tool_id']
                cursor.execute(
                    'INSERT INTO tool_usage (date, tool_id, act_id, order_id, ore_lav) '
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (date, tool_id, act_id, order_id, ore_lav)
                )
            db.commit()
            return redirect(url_for('accounting_hours.index'))

    return render_template('accounting_hours/create.html', act_types=act_types, acts=acts, people=people, anag_tools1=anag_tools1)

@bp.route('/accounting_hours/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    ts_record = get_ts_record(id)
    people_id = ts_record['people_id']
    date = ts_record['date']
      
    if ts_record['locked'] == True:
        error = 'Questa consuntivazione non può essere modificata.'
        flash(error)
        return redirect(url_for('accounting_hours.index'))
    else:
        data_plus_one = date + timedelta(days=1)
        oggi = datetime.today().date()
        if oggi > data_plus_one and g.role != "ADMIN":
            error = 'Questa consuntivazione non può essere modificata.'
            flash(error)
            return redirect(url_for('accounting_hours.index'))
    act_types = get_act_type_List()
    acts = get_actsFiltered(date)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        date = request.form['date']
        act_type_id = request.form.get('act_type_id')
        act_id = request.form.get('act_id')
        ore_lav = request.form['ore_lav']
        night = request.form.get('night')
        
        if night == None:
            night = 0
        print("night:")
        print(night)
        if act_type_id != "1":
            act_id = None
            order_id = None
        else:
            cursor.execute('SELECT p_order_id FROM activity ' 
                ' WHERE id=%s', (act_id,))
            result = cursor.fetchone()
            order_id = result['p_order_id']
        error = None

        if (not date) or (not act_type_id) or (not ore_lav):
            error = 'Compila tutti i campi obbligatori.'
        #if (act_type_id == "1") and (not act_id):
        #    error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            if (act_type_id != "1"):
                order_id = None
            cursor.execute(
               'UPDATE timesheet SET date = %s, act_type_id = %s, people_id = %s, order_id = %s, ore_lav = %s, night = %s, act_id = %s'
                ' WHERE id = %s',
                (date, act_type_id, people_id, order_id, ore_lav, night, act_id, id)
            )
            db.commit()
            return redirect(url_for('accounting_hours.index'))
    return render_template('accounting_hours/update.html', ts_record=ts_record, act_types=act_types, acts=acts)

@bp.route('/accounting_hours/<int:id>/delete', methods=('POST',))
@login_required 
def delete(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    ts_record = get_ts_record(id)
    if ts_record['locked'] == True:
        error = 'Questa consuntivazione non può essere cancellata.'
        flash(error)
    else:
        date = ts_record['date']
        data_plus_one = date + timedelta(days=1)
        oggi = datetime.today().date()
        if oggi > data_plus_one and g.role != "ADMIN":
            error = 'Questa consuntivazione non può essere cancellata.'
            flash(error)
        else:
            cursor.execute('DELETE FROM timesheet WHERE id = %s', (id,))
            db.commit()
    return redirect(url_for('accounting_hours.index'))

@bp.route('/accounting_hours/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    ts_record = get_ts_record(id)
    date = ts_record['date']
    acts = get_actsFiltered(date)
    act_types=get_act_type_List()
    anag_people = get_anag_people()
    return render_template('accounting_hours/detail.html', ts_record=ts_record, act_types=act_types, acts=acts, anag_people=anag_people)

@bp.route("/ts_sel_order/<date>", methods=('POST',))
@login_required
def sel_order(date):
    print("sel_order date: " + str(date))
    orderList = get_orderListFiltered(date)
    return (orderList)

def get_ts_record(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, date, act_type_id, people_id, order_id, ore_lav, night, locked' 
        ' FROM timesheet '
        ' WHERE id = %s',
        (id,)
    )
    ts_record = cursor.fetchone()
    if ts_record is None:
        abort(404, f"ts_record id {id} non esiste.")

    return ts_record

def get_act_type_List():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS act_type_id, description AS act_type_desc, short_code'
        ' FROM act_type '
    )
    act_type_List = cursor.fetchall()

    if act_type_List is None:
        abort(404, f"act_type_List è vuota.")
    return act_type_List

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

def get_anag_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(surname," ",name) AS name FROM people'
    )
    anag_people=cursor.fetchall()
    current_app.logger.debug("get_anag_people")
    current_app.logger.debug(anag_people)
    return anag_people

def get_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT id FROM people WHERE user_id=%s',(g.user_id,))
    people = cursor.fetchone()
    return(people)

def get_act_type_List2():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(id) AS id, GROUP_CONCAT(description) AS description '
        ' FROM act_type '
    )
    act_types = cursor.fetchone()

    if act_types is None:
        abort(404, f"act_types è vuota.")
    return act_types

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

def get_anag_tools_ore():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT t.id AS tool_id, CONCAT(brand," ",model, " ", license_plate) AS tool_name ' 
        ' FROM tool t INNER JOIN tool_type tt ON t.tool_type_id=tt.id '
        ' WHERE tt.cons_ore=1 AND t.discontinued=0 '
        ' ORDER BY brand,model ASC'
    )
    anag_tools1=cursor.fetchall()
    return anag_tools1