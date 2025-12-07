from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime, timedelta
from dateutil.easter import *

bp = Blueprint('timesheet', __name__)

@bp.route('/timesheet', methods=('GET', 'POST'))
@login_required
def index():
    
    if g.role != "ADMIN" and g.role != "TEAM_LEADER" and g.role != "SEGRETERIA":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    
    session["activity_first_page"] = 'Y'
    session["show_calendar"] = 'N'
   
    if not "timesheet_filter" in session:
        session["timesheet_filter"] = "wo_holidays"
        session["search"] = " WHERE act_type_id <> 2 "
    searchStr = session["search"]
    print("timesheet_filter: " + session["timesheet_filter"]) 
    if session["timesheet_filter"] == "wo_holidays":
        filterA = "wo_holidays"
    else:
        filterA = "with_holidays"
    print("filterA: " + filterA)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    current_app.logger.debug("searchStr 1: " + searchStr)
    current_app.logger.debug("session.get('search'): " + str(session.get('search')))
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT ts.id, ts.date as date, at.description as act_type, CONCAT(p.surname," ",p.name) as p_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, ts.ore_lav'
            ' FROM timesheet ts' 
            ' LEFT JOIN p_order o on ts.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN act_type at on ts.act_type_id = at.id'
            ' INNER JOIN people p on ts.people_id = p.id ' +
            searchStr + ") AS ts_tables" 
            )
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]

    if request.method == 'POST': 
        page = "1"
        filterA = request.form['filterA']
        session["timesheet_filter"] = filterA
        if filterA == "wo_holidays":
            searchStr = " WHERE act_type_id <> 2 "
        else:
            searchStr = ""
        print("filterA nella POST: " + filterA)
        searchDate = request.form['searchDate']
        searchCustomer = request.form['searchCustomer']
        searchPeople = request.form['searchPeople']
        if ((searchDate + searchCustomer + searchPeople) != "") and searchStr == "":
            searchStr = " WHERE "
        if (searchDate != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + "ts.date = '" + searchDate + "'"
        if (searchCustomer != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " c.full_name LIKE '%" + searchCustomer + "%'"
        if (searchPeople != ""):
            if (searchStr != " WHERE "):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " CONCAT(p.surname,\" \",p.name) LIKE '%" + searchPeople + "%'"
        #searchStr = searchStr.upper()
        current_app.logger.debug("searchStr 2: " + searchStr)
        session["search"] = searchStr
        current_app.logger.debug("session.search: " + session["search"])
        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT ts.id, ts.date as date, at.description as act_type, CONCAT(p.surname," ",p.name) as p_name, coalesce(CONCAT(c.full_name," - ",o.description), " - ") as p_order, ts.ore_lav'
            ' FROM timesheet ts' 
            ' LEFT JOIN p_order o on ts.order_id = o.id'
            ' LEFT JOIN customer c on o.customer_id = c.id'
            ' INNER JOIN act_type at on ts.act_type_id = at.id'
            ' INNER JOIN people p on ts.people_id = p.id ' +
            searchStr + ") AS ts_tables" 
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
            str(searchStr) +
            ' ORDER BY ts.date DESC, p_name ASC LIMIT %s OFFSET %s', 
            (per_page, offset)
        )
    ts_records = cursor.fetchall()
    
    return render_template('timesheet/index.html', ts_records=ts_records, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr, filterA=filterA)

@bp.route('/timesheet/create', methods=('GET', 'POST'))
@login_required
def create():
    anag_people = get_anag_people()
    act_types = get_act_type_List2()
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
        people_ids = request.form['input_people_ids']
        #print("people_ids: " + people_ids)
        
        error = None

        if (not date) or (not people_ids):
            error = 'Compila tutti i campi obbligatori.'
        act_type_ids_sel = request.form['act_type_ids_sel']
        if act_type_ids_sel == "":
            error = 'Devi inserire almeno una presenza.'
        if error is not None:
            flash(error)
        else:
            order_ids_sel = request.form['order_ids_sel']
            ore_lavs_sel = request.form['ore_lavs_sel']
            night_sel = request.form['night_sel']
            act_type_ids_sel_arr = act_type_ids_sel.split(",")
            order_ids_sel_arr = order_ids_sel.split(",")
            ore_lavs_sel_arr = ore_lavs_sel.split(",")
            night_sel_arr = night_sel.split(",")

            db = get_db()
            people_ids_arr = people_ids.split(",") 
            for people_id in people_ids_arr:
                k=0
                while k < len(act_type_ids_sel_arr):
                    act_type_id = int(act_type_ids_sel_arr[k])
                    
                    if order_ids_sel_arr[k] != "":
                        order_id = int(order_ids_sel_arr[k])
                    else:
                        order_id = None
                    if ore_lavs_sel_arr[k] != "":
                        ore_lav = float(ore_lavs_sel_arr[k])
                    else:
                        ore_lav = 0
                    if night_sel_arr[k] == "true":
                        night = 1
                    else:
                        night = 0
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO timesheet (date, act_type_id, people_id, order_id, ore_lav, night)'
                        ' VALUES (%s, %s, %s, %s, %s, %s)',
                        (date, act_type_id, people_id, order_id, ore_lav, night)
                    )
                    k = k + 1
            db.commit()
            return redirect(url_for('timesheet.index'))

    return render_template('timesheet/create.html', act_types=act_types, orders=orders, anag_people=anag_people)

@bp.route('/timesheet/create_daysoff', methods=('GET', 'POST'))
@login_required
def create_daysoff():
    anag_people = get_anag_people()
    format = '%Y-%m-%d'
    date1 = datetime.today().strftime(format)
    date2 = datetime.today().strftime(format)

    if request.method == 'POST':
        date1 = request.form['date1']
        date2 = request.form['date2']
        #print("Range di date: " + date1 + " - " + date2)
        date1_dt = datetime.strptime(date1, format)
        date2_dt = datetime.strptime(date2, format)
        #print("Range di date: " + date1_dt.strftime(format) + " - " + date2_dt.strftime(format))
        people_ids = request.form['input_people_ids']
        act_type_id = 2
        
        error = None

        if (not date1) or (not date2) or (not people_ids):
            error = 'Compila tutti i campi obbligatori.'
       
        if error is not None:
            flash(error)
        else:
            db = get_db()
            people_ids_arr = people_ids.split(",") 
            date_dt = date1_dt
            while date_dt <= date2_dt:
                date = date_dt.strftime(format)
                #print("Data ferie: " + date)
                year = date_dt.year
                month = date_dt.month
                dayNum = date_dt.day
                #Se il giorno è feriale (weekday da 0 a 4 cioé LUN-VER e non è festività)
                if date_dt.weekday() <= 4 and not isHoliday(year,month,dayNum):
                    #print("Data feriale: " + date)
                    print("date_dt.weekday: " + str(date_dt.weekday()))
                    if date_dt.weekday() == 4:
                        ore_lav = 7
                    else:
                        ore_lav = 8
                    print("ore_lav: " + str(ore_lav))
                    for people_id in people_ids_arr:
                    
                        cursor = db.cursor(dictionary=True)
                        cursor.execute(
                            'INSERT INTO timesheet (date, act_type_id, people_id, ore_lav)'
                            ' VALUES (%s, %s, %s, %s)',
                            (date, act_type_id, people_id, ore_lav)
                        )
                        db.commit()
                        #print("scriverebbe un record in timesheet per people_id=" + str(people_id))

                date_dt = date_dt + timedelta(days=1)
                #print("date_dt incrementata di un giorno: " + date_dt.strftime(format))
            return redirect(url_for('timesheet.index'))

    return render_template('timesheet/create_daysoff.html', anag_people=anag_people)


@bp.route('/timesheet/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    current_app.logger.debug("id: " + str(id))
    ts_record = get_ts_record(id)
    if ts_record['locked'] == True:
        error = 'Questa consuntivazione non può essere modificata.'
        flash(error)
        return redirect(url_for('timesheet.index'))
    act_type_List=get_act_type_List()
    anag_people = get_anag_people()
    date = ts_record['date']
    data_plus_one = date + timedelta(days=1)
    oggi = datetime.today().date()
    if oggi > data_plus_one and g.role != "ADMIN":
        error = 'Questa consuntivazione non può essere modificata.'
        flash(error)
        return redirect(url_for('timesheet.index'))
    #orderList = get_orderList() #Non filtrata
    orderList = get_orderListFiltered(date)

    if request.method == 'POST':
        date = request.form['date']
        act_type_id = request.form['input_act_type_id']
        people_id = request.form['input_people_id']
        order_id = request.form['input_order_id']
        ore_lav = request.form['ore_lav']
        night = request.form['input_night']
        
        error = None
        print("Debug:")
        print(date)
        print(act_type_id)
        print(people_id)
        print(ore_lav)
        print(order_id)

        if (not date) or (not act_type_id) or (not people_id) or (not ore_lav):
            error = 'Compila tutti i campi obbligatori.'
        if (act_type_id == "1") and (not order_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            if (act_type_id != "1"):
                order_id = None
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
               'UPDATE timesheet SET date = %s, act_type_id = %s, people_id = %s, order_id = %s, ore_lav = %s, night = %s'
                ' WHERE id = %s',
                (date, act_type_id, people_id, order_id, ore_lav, night, id)
            )
            db.commit()
            return redirect(url_for('timesheet.index'))
    return render_template('timesheet/update.html', ts_record=ts_record, act_type_List=act_type_List, orderList=orderList, anag_people=anag_people)

@bp.route('/timesheet/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    current_app.logger.debug("id: " + str(id))
    ts_record = get_ts_record(id)
    act_type_List=get_act_type_List()
    anag_people = get_anag_people()
    #orderList = get_orderList()
    date = ts_record['date']
    orderList = get_orderListFiltered(date)

    if request.method == 'POST':
        date = request.form['date']
        act_type_id = request.form['input_act_type_id']
        people_id = request.form['input_people_id']
        order_id = request.form['input_order_id']
        ore_lav = request.form['ore_lav']
        
        error = None

        if (not date) or (not act_type_id) or (not people_id) or (not ore_lav):
            error = 'Compila tutti i campi obbligatori.'
        if (act_type_id == "1") and (not order_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            if (act_type_id != "1"):
                order_id = None
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO timesheet (date, act_type_id, people_id, order_id, ore_lav)'
                ' VALUES (%s, %s, %s, %s, %s)',
                (date, act_type_id, people_id, order_id, ore_lav)
            )
            db.commit()
            return redirect(url_for('timesheet.index'))
    return render_template('timesheet/update.html', ts_record=ts_record, act_type_List=act_type_List, orderList=orderList, anag_people=anag_people)


@bp.route('/timesheet/<int:id>/delete', methods=('POST',))
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
    return redirect(url_for('timesheet.index'))


@bp.route('/timesheet/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    ts_record = get_ts_record(id)
    orderList = get_orderList()
    act_type_List=get_act_type_List()
    anag_people = get_anag_people()
    return render_template('timesheet/detail.html', ts_record=ts_record, act_type_List=act_type_List, orderList=orderList, anag_people=anag_people, show_calendar = session["show_calendar"])

@bp.route("/ts_sel_order/<date>", methods=('POST',))
@login_required
def sel_order(date):
    #orderList=get_orderListFiltered(date)
    #results = [tuple(row) for row in orderList]
    orderList = get_orderListFiltered(date)
    #print(jsonify(results))
    #return (jsonify(results))
    #print(orderList)
    return (orderList)

@bp.route("/ts_sel_order2/<date>", methods=('POST',))
@login_required
def sel_order2(date):
    #orderList = get_orderListFiltered2(date)
    orders = get_orderListFiltered2(date)
    order_ids = orders["order_id"]
    order_descs = orders["order_desc"]
    #Aggiungo un elemento vuoto per la jsgrid dell'interfaccia utente
    order_ids = "," + order_ids 
    order_descs = "|§|" + order_descs
    orderList = {"order_id" : order_ids, "order_desc" : order_descs}
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
        'SELECT id, description, short_code'
        ' FROM act_type '
    )
    act_type_List = cursor.fetchall()

    if act_type_List is None:
        abort(404, f"act_type_List è vuota.")
    return act_type_List

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

def get_anag_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(surname," ",name) AS name FROM people WHERE cessato=0 ORDER BY surname,name ASC'
    )
    anag_people=cursor.fetchall()
    return anag_people

def get_anag_people2():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(id order by surname,name) AS id, GROUP_CONCAT(CONCAT(surname," ",name) order by surname,name) AS name FROM people WHERE cessato=0'
    )
    anag_people=cursor.fetchone()
    return anag_people

def isHoliday(year,month,dayNum):
    #Calcola tutte le festività civili italiane compresa Pasquetta
    #Include anche la festa patronale di Mapello (29 settembre) 
    easter_date = easter(year)
    easter_monday_date = easter_date + timedelta(days=1)
    easter_monday_dayNum = easter_monday_date.day
    easter_monday_Month = easter_monday_date.month

    if (month == 1 and dayNum == 1) or \
        (month == 1 and dayNum == 6) or \
        (month == 4 and dayNum == 25) or \
        (month == 5 and dayNum == 1) or \
        (month == 6 and dayNum == 2) or \
        (month == 8 and dayNum == 15) or \
        (month == 9 and dayNum == 29) or \
        (month == 11 and dayNum == 1) or \
        (month == 12 and dayNum == 8) or \
        (month == 12 and dayNum == 25) or \
        (month == 12 and dayNum == 26) or \
        (month == easter_monday_Month and dayNum == easter_monday_dayNum):
        isHoliday = True
    else:
        isHoliday = False
    
    #print("mese " + str(month) + " giorno " + str(dayNum))
    #print(str(isHoliday))
    return isHoliday