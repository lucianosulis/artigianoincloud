from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime, timedelta
from dateutil.easter import *

from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import requests
from .geo_utils import road_distance_km

bp = Blueprint('tool_usage', __name__)

@bp.route('/tool_usage', methods=('GET', 'POST'))
@login_required
def index():
    
    session["activity_first_page"] = 'Y'
   
    if not "search_tu" in session:
        session["search_tu"] = ""
    searchStr = session["search_tu"]
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    current_app.logger.debug("searchStr 1: " + searchStr)
    current_app.logger.debug("session.get('search'): " + str(session.get('search_tu')))
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
            session["search_tu"] = searchStr
        current_app.logger.debug("searchStr 2: " + searchStr)
        session["search_tu"] = searchStr
        current_app.logger.debug("session.search: " + session["search_tu"])
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
    ld_anag_tools1 = get_anag_tools_ore()
    anag_tools1 = json.dumps(ld_anag_tools1) #json
    ld_anag_tools2 = get_anag_tools_km()
    anag_tools2 = json.dumps(ld_anag_tools2) #json
    date = datetime.today().strftime('%Y-%m-%d')
    acts_ld = get_actsFiltered(date) #lista dizionari
    acts_ld.insert(0, {'act_desc': '','act_id': 0,'p_order_id': 0 })
    acts = json.dumps(acts_ld) #json

    if request.method == 'POST':
        date = request.form['date']

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
        
        dati_json_stringa2 = request.form.get('dati_griglia_json2')
        #print(dati_json_stringa2)
        dati_griglia2 = []
        if dati_json_stringa2:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia2 = json.loads(dati_json_stringa2)
                #print(dati_griglia2)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia 2")
                error = 'Errore nella decodifica dei dati JSON della griglia 2.'
        error = None

        if (not date):
            error = 'Compila tutti i campi obbligatori.'
        if (not dati_griglia1) and (not dati_griglia2):
            error = 'Devi inserire almeno un utilizzo mezzo.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
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
            for record in dati_griglia2:
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                act_id = record['act_id']
                cursor.execute('SELECT p_order_id FROM activity ' 
                    ' WHERE id=%s', (act_id,))
                result = cursor.fetchone()
                order_id = result['p_order_id']  
                km = record['km']      
                tool_id = record['tool_id']
                cursor.execute(
                    'INSERT INTO tool_usage (date, tool_id, act_id, order_id, km) '
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (date, tool_id, act_id, order_id, km)
                )
            db.commit()
            return redirect(url_for('tool_usage.index'))

    return render_template('tool_usage/create.html', acts=acts, anag_tools1=anag_tools1, anag_tools2=anag_tools2)

@bp.route('/tool_usage/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    tu_record = get_tu_record(id)
    tool_name = get_tool_name(tu_record['tool_id'])
    cons_type = get_cons_type(id) #Lista flag ore km. Es. [1,0] vuol dire ore sì, km no
    cons_ore = cons_type['cons_ore'] 
    cons_km = cons_type['cons_km'] 
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari

    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        date = request.form.get('date')
        act_id = request.form.get('act_id')
        if cons_ore == 1:
            ore_lav = request.form['ore_lav']
            if ore_lav == "":
                ore_lav = 0
        else:
            ore_lav = 0
        if cons_km == 1:
            km = request.form['km']
            if km == "":
                km = 0
        else:
            km = 0
        
        error = None

        if (not date)  or (not act_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            cursor.execute('SELECT p_order_id FROM activity ' 
                ' WHERE id=%s', (act_id,))
            result = cursor.fetchone()
            order_id = result['p_order_id']
            cursor.execute(
               'UPDATE tool_usage SET date = %s, act_id = %s, order_id = %s, ore_lav = %s, km = %s '
                ' WHERE id = %s',
                (date, act_id, order_id, ore_lav, km, id)
            )
            db.commit()
            return redirect(url_for('tool_usage.index'))
    return render_template('tool_usage/update.html', tu_record=tu_record, tool_name=tool_name, acts=acts, cons_ore=cons_ore,cons_km=cons_km )

@bp.route('/tool_usage/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    tu_record = get_tu_record(id)
    tool_id = tu_record['tool_id']
    tool_name = get_tool_name(tu_record['tool_id'])
    cons_type = get_cons_type(id) #Lista flag ore km. Es. [1,0] vuol dire ore sì, km no
    cons_ore = cons_type['cons_ore'] 
    cons_km = cons_type['cons_km'] 
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari

    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        date = request.form.get('date')
        act_id = request.form.get('act_id')
        if cons_ore == 1:
            ore_lav = request.form['ore_lav']
            if ore_lav == "":
                ore_lav = 0
        else:
            ore_lav = 0
        if cons_km == 1:
            km = request.form['km']
            if km == "":
                km = 0
        else:
            km = 0
        cursor.execute('SELECT p_order_id FROM activity ' 
                    ' WHERE id=%s', (act_id,))
        result = cursor.fetchone()
        order_id = result['p_order_id']
                
        error = None

        if (not date)  or (not act_id):
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
    return render_template('tool_usage/update.html', tu_record=tu_record, tool_name=tool_name, acts=acts, cons_ore=cons_ore,cons_km=cons_km )


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
    tool_name = get_tool_name(tu_record['tool_id'])
    date = tu_record['date']
    acts = get_actsFiltered(date) #lista dizionari
    return render_template('tool_usage/detail.html', tu_record=tu_record, acts=acts, tool_name=tool_name)

@bp.route('/tool_usage/tool_route', methods=('GET','POST'))
@login_required
def tool_route():  
    #Prendo come data di partenza quella successiva all'ultimo record con Km
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('select date from tool_usage tu where km <> 0 '
                    ' ORDER BY date DESC LIMIT 1 ')
    result=cursor.fetchone()
    if (not result):
        date_obj = datetime.today() + timedelta(days=-1)
    else:
        date_obj = result['date']
    date_start = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    #print(f"date_start: {date_start}")
    #date_start= datetime.today().strftime('%Y-%m-%d')
    #Prendo come data fine quella di oggi (modificabile sulla form)
    date_end = datetime.today().strftime('%Y-%m-%d')
    if request.method == 'POST':
        print("POST salvataggio dati")
        error = None
        date_start= request.form['date_start']
        date_end =  request.form['date_end']
        dati_json_stringa3 = request.form.get('dati_griglia_json3')
        #print(dati_json_stringa2)
        dati_griglia3 = []
        if dati_json_stringa3:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia3 = json.loads(dati_json_stringa3)
                #print(dati_griglia3)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia 3")
                error = 'Errore nella decodifica dei dati JSON della griglia 3.'

        if (not dati_griglia3) :
            error = 'Non ci sono mezzi da registrare.'
        if error is not None:
            flash(error)
        else:
            for record in dati_griglia3:
                print(record)
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                date = record['date']
                act_id = record['act_id']
                order_id = record['order_id']       
                tool_id = record['tool_id']
                km = record['km']
                print(f"Km={km}")
                cursor.execute(
                    'INSERT IGNORE INTO tool_usage (date, tool_id, act_id, order_id, km) '
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (date, tool_id, act_id, order_id, km)
                )
                db.commit()
            return redirect(url_for('tool_usage.index'))

    return render_template('tool_usage/tool_route.html', date_start=date_start, date_end=date_end)

@bp.route('/tool_usage/route_calc/<date_start>/<date_end>', methods=('POST',))
@login_required
def route_calc(date_start,date_end): 
    print("Sono in route_calc")
    error = None
    data_returned = []
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT latitude,longitude from company WHERE id=1')
    result = cursor.fetchone()
    #coordinate di partenza
    lat1 = result['latitude']
    lon1 = result['longitude']
    #estraggo i mezzi a Km utilizzati nell'intervallo di date
    #I Km sono messi a zero per ora
    cursor.execute(
        'SELECT t.date as date, a.id as act_id, CONCAT(c.full_name, " - ", a.title) AS act_desc, '
        ' o.id as order_id, tl.id as tool_id, CONCAT(brand," ",model, " ", license_plate) AS tool_name, '
        ' CONCAT(s.address,", ",s.city) as arrival_site, 0 AS km, '
        ' s.latitude, s.longitude '
        ' from activity a '
        ' inner join site s on a.site_id = s.id '
        ' inner join p_order o ON a.p_order_id = o.id '
        ' inner join customer c ON o.customer_id = c.id '
        ' inner join rel_team_activity rta on rta.activity_id = a.id '
        ' inner join team t on rta.team_id = t.id '
        ' inner join rel_team_tool rtt on rtt.team_id = t.id '
        ' inner join tool tl on rtt.tool_id  = tl.id '
        ' inner join tool_type tt on tl.tool_type_id = tt.id '
        ' where t.date >= %s and t.date <= %s and tt.cons_km = 1', (date_start,date_end))
    
    tools = cursor.fetchall()
    #print(tools)
    
    for tool in tools:
        tool_date = tool['date']
        tool['date'] = tool_date.strftime('%Y-%m-%d')
        # Utilizza le API pubbliche di OSRM
        try:
            lat2 = tool['latitude']
            lon2 = tool['longitude']
            if (not lat2) or (not lon2): 
                tool['km'] = 0
            else:
                url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
                r = requests.get(url)
                data = r.json()
                # La distanza restituita è in metri
                distanza_metri = data['routes'][0]['distance']
                dist_stradale = round(distanza_metri / 1000 * 2) 
                tool['km'] = dist_stradale
        except Exception as e:
            flash(f"Errore durante l'esecuzione: {e}")
            tool['km'] = 0
        data_returned.append(tool)
    try:
        risposta_json = jsonify(data_returned)
        print("JSON creato con successo")
        return risposta_json
    except Exception as e:
        print(f"ERRORE FATALE durante la creazione del JSON: {e}")
        return jsonify({"error": str(e)}), 500

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

def get_anag_tools_km():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT t.id AS tool_id, CONCAT(brand," ",model, " ", license_plate) AS tool_name ' 
        ' FROM tool t INNER JOIN tool_type tt ON t.tool_type_id=tt.id '
        ' WHERE tt.cons_km=1 AND t.discontinued=0 '
        ' ORDER BY brand,model ASC'
    )
    anag_tools2=cursor.fetchall()
    return anag_tools2

def get_tool_name(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT CONCAT(brand," ",model, " ", license_plate) AS tool_name ' 
        ' FROM  tool ' 
        ' WHERE id=%s ',(id,))
    result=cursor.fetchone()
    tool_name = result['tool_name']
    return tool_name

def get_cons_type(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT tt.cons_ore,tt.cons_km ' 
        ' FROM  tool_usage tu ' 
        ' INNER JOIN tool t ON t.id=tu.tool_id ' 
        ' INNER JOIN tool_type tt ON t.tool_type_id=tt.id '
        ' WHERE tu.id=%s ',(id,))
    cons_type=cursor.fetchone()
    return cons_type

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
