from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date
from datetime import datetime
#import requests

bp = Blueprint('people_available', __name__)

@bp.route('/people_available', methods=('GET', 'POST'))
@login_required
def index():
    session["show_calendar"] = 'N'
    if not "people_available_filter" in session:
        searchStr = ""
    else:
        searchStr = session["people_available_filter"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT pa.id, pa.start AS start, pa.end AS end, CONCAT(p.surname," ",p.name) AS name '
             ' FROM people_available pa'
             ' INNER JOIN people p ON pa.people_id = p.id '
             +
            searchStr + ") AS availabilities"
            )
    
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')

    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 
        searchDate = request.form['searchDate']
        searchPeople = request.form['searchPeople']
        if ((searchDate + searchPeople) != ""):
            searchStr = " WHERE "
        else:
            searchStr = ""
        if (searchDate != ""):
            searchStr = searchStr + "start = '" + searchDate +"'"
        if (searchPeople != ""):
            if (searchDate != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " CONCAT(surname,' ',name) LIKE '%" + searchPeople.upper() + "%'"
        session["people_available_filter"] = searchStr

        #print("searchStr")
        #print(searchStr)
        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT pa.id, pa.start AS start, pa.end AS end, CONCAT(p.surname," ",p.name) AS name '
             ' FROM people_available pa'
             ' INNER JOIN people p ON pa.people_id = p.id ' +
            searchStr + ") AS availabilities"
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    if session["people_available_first_page"] == 'N':
        if page == None:
            page = 1
        offset = (int(page)-1) * per_page
    else:
        #Pagina iniziale (session["people_available_first_page"] == 'Y')
        #Individuo la pagina più vicina alla data odierna
        today = date.today()
        query = ('SELECT COUNT(*) AS count FROM '
                ' (SELECT pa.id, pa.start AS start, pa.end AS end, CONCAT(p.surname," ",p.name) AS name '
                ' FROM people_available pa'
                ' INNER JOIN people p ON pa.people_id = p.id ')
        if searchStr == "":
            query = query + ' WHERE start < %s) AS availabilities'
        else:
            query = query + searchStr +  ' AND start < %s) AS availabilities'
        #print(query)
        cursor.execute(query,(today,))
        rowCount = cursor.fetchone()
        number_to_bypass = rowCount['count']   
        page_num = int((number_to_bypass / per_page)) + 1 
        #print ("page_num: " + str(page_num))
        offset = (int(page_num)-1) * per_page
        page = str(page_num) 
        session["people_available_first_page"] = 'N'
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    #print(str(per_page) + " ----- " + str(offset))
    cursor.execute(
            'SELECT pa.id, DATE_FORMAT(pa.start,"%d/%m/%y") AS start, DATE_FORMAT(pa.end,"%d/%m/%y") AS end, CONCAT(p.surname," ",p.name) AS name '
            ' FROM people_available pa '
            ' INNER JOIN people p ON pa.people_id = p.id ' +
             searchStr +
            ' ORDER BY pa.start ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
    availabilities = cursor.fetchall()
    
    return render_template('people_available/index.html', availabilities=availabilities, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/people_available/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("people_available.index"))
    anag_people = get_anag_people()
    
    if request.method == 'POST':
        people_ids = request.form.getlist('people_ids')
        start = request.form['start']
        end = request.form['end']
        error = None

        if (not start) or (not end) or (not people_ids):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine disponibilità deve essere maggiore o uguale alla data di inizio.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            for people_id in people_ids:
                #Creo il nuovo record per la disponibilità
                cursor.execute(
                    'INSERT INTO people_available (people_id, start, end)'
                    ' VALUES (%s, %s, %s)',
                    (people_id, start, end)
                )
                db.commit()

            return redirect(url_for('people_available.index'))

    return render_template('people_available/create.html', anag_people=anag_people)

@bp.route('/people_available/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("people_available.index"))
    anag_people = get_anag_people()

    if request.method == 'POST':
        people_ids = request.form.getlist('people_ids')
        start = request.form['start']
        end = request.form['end']
    
        error = None

        if (not start) or (not end) or (not people_ids):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine disponibilità deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Creo il nuovo record per l'attività
            for people_id in people_ids:
                #Creo il nuovo record per la disponibilità
                cursor.execute(
                    'INSERT INTO people_available (people_id, start, end)'
                    ' VALUES (%s, %s, %s)',
                    (people_id, start, end)
                )
            db.commit()
            
            return redirect(url_for('cal_availability.show_cal'))
    show_calendar =  session["show_calendar"]
    return render_template('people_available/create_from_cal.html', anag_people=anag_people,sel_date=sel_date, show_calendar=show_calendar)

@bp.route('/people_available/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("people_available.index"))
    show_calendar =  session["show_calendar"]
    availability = get_availability(id)
    anag_people = get_anag_people()
        
    if request.method == 'POST': 
        people_id = request.form['people_id']
        start = request.form['start']
        end = request.form['end']

        error = None

        if (not people_id) or (not start) or (not end):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine disponibilità deve essere maggiore o uguale alla data di inizio.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE people_available SET people_id = %s, start = %s, end = %s '
                ' WHERE id = %s',
                (people_id, start, end, id)
            )
            db.commit()
            if show_calendar == "Y":
                return redirect(url_for('cal_availability.show_cal'))
            else:
                return redirect(url_for('people_available.index'))
    
    print("show_calendar: " + show_calendar)
    return render_template('people_available/update.html', availability=availability, anag_people=anag_people, show_calendar=show_calendar)

@bp.route('/people_available/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("people_available.index"))
    availability = get_availability(id)
    anag_people = get_anag_people()
    
    if request.method == 'POST':
        people_id = request.form['people_id']
        start = request.form['start']
        end = request.form['end']
        
        error = None

        if (not people_id) or (not start) or (not end):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO people_available (people_id, start, end)'
                    ' VALUES (%s, %s, %s)',
                    (people_id, start, end)
            )
            db.commit()
            
            return redirect(url_for('people_available.index'))
    return render_template('people_available/duplicate.html', anag_people=anag_people, availability=availability)

@bp.route('/people_available/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("people_available.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM people_available WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('people_available.index'))


@bp.route('/people_available/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    availability = get_availability(id)
    show_calendar =  session["show_calendar"]
    return render_template('people_available/detail.html', availability=availability, show_calendar=show_calendar)

def get_availability(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT  pa.id, pa.people_id, pa.start, pa.end, CONCAT(p.surname, " ",p.name) as name'
        ' FROM people_available pa ' 
        ' INNER JOIN people p ON pa.people_id = p.id '
        ' WHERE pa.id = %s',
        (id,)
    )
    availability = cursor.fetchone()
    if availability is None:
        abort(404, f"people_available id {id} non esiste.")

    return availability

def get_anag_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(surname," ",name) AS name FROM people ' 
        ' WHERE cessato=0 and (type="C" or type="P") '
        ' ORDER BY surname,name ASC'
    )
    anag_people=cursor.fetchall()
    #print(anag_people)
    return anag_people