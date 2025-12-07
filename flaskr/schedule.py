from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session, send_file
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date
from io import BytesIO
import io

#import requests

bp = Blueprint('schedule', __name__)

@bp.route('/schedule', methods=('GET', 'POST'))
@login_required
def index():
    session["show_calendar"] = 'N'
    if not "schedule_filter" in session:
        searchStr = ""
    else:
        searchStr = session["schedule_filter"]
        current_app.logger.debug("1 - schedule_filter: " + session["schedule_filter"])
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT s.id, s.description, s.due_date, s.done, st.type '
            ' FROM schedule s'
            ' INNER JOIN schedule_type st ON s.schedule_type_id = st.id ' +
            searchStr + ") AS schedules"
            )
    
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')

    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 
        current_app.logger.debug("Sono nella POST")
        searchDate = request.form['searchDate']
        searchDescription = request.form['searchDescription']
        searchType = request.form['searchType']
        current_app.logger.debug("searchDate: " + searchDate)
        current_app.logger.debug("searchDescription: " + searchDescription)
        current_app.logger.debug("searchType: " + searchType)
        if ((searchDate + searchDescription + searchType) != ""):
            searchStr = " WHERE "
        else:
            searchStr = ""
        if (searchDate != ""):
            searchStr = searchStr + "due_date = '" + searchDate +"'"
        if (searchDescription != ""):
            if (searchDate != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " description LIKE '%" + searchDescription.upper() + "%'"
        if (searchType != ""):
            if (searchDate != "" or searchDescription != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " st.type LIKE '%" + searchType.upper() + "%'"
        #searchStr = searchStr.upper()
        current_app.logger.debug("searchStr: " + searchStr)
        #print("searchStr: " + searchStr)
        session["schedule_filter"] = searchStr

        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT s.id, s.description, s.due_date, s.done, st.type '
            ' FROM schedule s'
            ' INNER JOIN schedule_type st ON s.schedule_type_id = st.id ' +
            searchStr + ") AS schedules"
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    current_app.logger.debug("total: " + str(total))  
    #print("schedule_first_page: " + session["schedule_first_page"])  
    if session["schedule_first_page"] == 'N':
        if page == None:
            page = 1
        offset = (int(page)-1) * per_page
    else:
        #Pagina iniziale (session["schedule_first_page"] == 'Y')
        #Individuo la pagina più vicina alla data odierna
        today = date.today()
        query = ('SELECT COUNT(*) AS count FROM '
            ' (SELECT s.id, s.description, s.due_date, s.done, st.type '
            ' FROM schedule s'
            ' INNER JOIN schedule_type st ON s.schedule_type_id = st.id ')
        if searchStr == "":
            query = query + ' WHERE due_date < %s) AS schedules'
        else:
            query = query + searchStr +  ' AND due_date < %s) AS schedules'
        print(query)
        cursor.execute(query,(today,))
        rowCount = cursor.fetchone()
        number_to_bypass = rowCount['count']   
        page_num = int((number_to_bypass / per_page)) + 1 
        print ("page_num: " + str(page_num))
        offset = (int(page_num)-1) * per_page
        page = str(page_num) 
        session["schedule_first_page"] = 'N'
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    print(str(per_page) + " ----- " + str(offset))
    cursor.execute(
            'SELECT s.id, s.description, DATE_FORMAT(s.due_date,"%d/%m/%y") AS due_date, s.done, st.type '
            ' FROM schedule s'
            ' INNER JOIN schedule_type st ON s.schedule_type_id = st.id ' 
             +
            searchStr +
            ' ORDER BY s.due_date ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
    schedules = cursor.fetchall()
    
    return render_template('schedule/index.html', schedules=schedules, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/schedule/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("schedule.index"))
    anag_type = get_anag_type()
    if request.method == 'POST':
        description = request.form['description']
        due_date = request.form['due_date']
        schedule_type_id = request.form['input_schedule_type_id']
        notes = request.form['notes']
       
        error = None
        if (not due_date) or (not schedule_type_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Creo il nuovo record per la manutenzione
            cursor.execute(
                'INSERT INTO schedule (description, due_date, schedule_type_id, notes)'
                ' VALUES (%s, %s, %s, %s)',
                (description, due_date, schedule_type_id, notes)
            )
            db.commit()
            return redirect(url_for('schedule.index'))

    return render_template('schedule/create.html', anag_type=anag_type)

@bp.route('/schedule/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("schedule.index"))
    anag_type = get_anag_type()
    if request.method == 'POST':
        description = request.form['description']
        due_date = request.form['due_date']
        schedule_type_id = request.form['input_schedule_type_id']
        notes = request.form['notes']
    
        error = None

        if (not due_date) or (not schedule_type_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Creo il nuovo record per la manutenzione
            cursor.execute(
                'INSERT INTO schedule (description, due_date, schedule_type_id, notes)'
                ' VALUES (%s, %s, %s, %s)',
                (description, due_date, schedule_type_id, notes)
            )
            db.commit()
            
            return redirect(url_for('cal_schedule.show_cal'))

    return render_template('schedule/create_from_cal.html', anag_type=anag_type, sel_date=sel_date)

@bp.route('/schedule/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("schedule.index"))
    current_app.logger.debug("id: " + str(id))
    schedule = get_schedule(id)
    show_calendar = session["show_calendar"]
    anag_type = get_anag_type()
    if request.method == 'POST':
        description = request.form['description']
        due_date = request.form['due_date']
        schedule_type_id = request.form['input_schedule_type_id']
        notes = request.form['notes']
        error = None

        if (not due_date) or (not schedule_type_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE schedule SET description = %s, due_date = %s, schedule_type_id = %s, notes = %s'
                ' WHERE id = %s',
               (description, due_date, schedule_type_id, notes, id)
            )
            db.commit()
            if show_calendar == "Y":
                 return redirect(url_for('cal_schedule.show_cal'))
            else:
                return redirect(url_for('schedule.index'))
    return render_template('schedule/update.html', schedule=schedule, anag_type=anag_type, show_calendar=show_calendar)

@bp.route('/schedule/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("schedule.index"))
    current_app.logger.debug("id: " + str(id))
    schedule = get_schedule(id)
    anag_type = get_anag_type()    
    if request.method == 'POST':
        description = request.form['description']
        due_date = request.form['due_date']
        schedule_type_id = request.form['input_schedule_type_id']
        notes = request.form['notes']
        error = None

        if (not due_date) or (not schedule_type_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO schedule (description, due_date, schedule_type_id, notes)'
                ' VALUES (%s, %s, %s, %s)',
                (description, due_date, schedule_type_id, notes)
            )
            db.commit()
           
            return redirect(url_for('schedule.index'))
    current_app.logger.debug("Sto per fare la return da duplicate")
    return render_template('schedule/duplicate.html', schedule=schedule, anag_type=anag_type )

@bp.route('/schedule/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("schedule.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM schedule WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('schedule.index'))


@bp.route('/schedule/<int:id>/detail', methods=('GET','POST'))
@login_required
def detail(id): 
    schedule = get_schedule(id) 
    show_calendar = session["show_calendar"]
    if request.method == 'POST':
        if g.role != "ADMIN":
            error = 'Non sei autorizzato a questa funzione.'
            flash(error)
            return redirect(url_for("schedule.index"))
        error = None
        
    return render_template('schedule/detail.html', schedule=schedule, show_calendar=show_calendar)    

@bp.route('/schedule/<int:id>/to_do', methods=('POST',))
@login_required
def to_do(id):
    current_app.logger.debug("to_do dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE schedule SET done = False'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "to_do"

@bp.route('/schedule/<int:id>/done', methods=('POST',))
@login_required
def done(id):
    current_app.logger.debug("done dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE schedule SET done = True'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "done"

def get_schedule(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id, s.description, s.due_date, s.done, s.notes,  '
                   'st.type, s.schedule_type_id'
            ' FROM schedule s'
            ' INNER JOIN schedule_type st ON s.schedule_type_id = st.id '
        ' WHERE s.id = %s',
        (id,)
    )
    schedule = cursor.fetchone()
    if schedule is None:
        abort(404, f"schedule id {id} non esiste.")
    print("get_schedule:")
    return schedule

def get_anag_type():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS type_id, type AS type_name FROM schedule_type  ORDER BY id'
    )
    anag_type=cursor.fetchall()
    return anag_type