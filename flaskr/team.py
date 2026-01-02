#Aggiungo commento per provare la commit GITHUB

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date, datetime, timedelta
#import requests

bp = Blueprint('team', __name__)

@bp.route('/team', methods=('GET', 'POST'))
@login_required
def index():
    session["show_calendar"] = 'N'
    today = date.today()
    if session["team_first_page"] == 'Y':
        filterA = "future_only"
        searchStr = " WHERE date >= '" + today.strftime("%Y-%m-%d") + "'"
        session["team_filter"] = searchStr
        session["team_filterA"] = filterA
        session["team_first_page"] = "N"
    else:
        searchStr = session["team_filter"]
        filterA =  session["team_filterA"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = 'SELECT COUNT(*) AS count FROM team'
    query = query + searchStr
    print(query)
    cursor.execute(query) 
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    if page == None:
            page = 1
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    offset = (int(page)-1) * per_page
    
    if request.method == 'POST': 
        searchDate = request.form['searchDate']
        searchTitle = request.form['searchTitle']
        filterA = request.form.get("filterA")
        print("filterA: " + filterA)
        session["team_filterA"] = filterA
        if ((searchDate + searchTitle) != ""):
            searchStr = " WHERE "
        else:
            searchStr = ""
        if (searchDate != ""):
            searchStr = searchStr + "date = '" + searchDate +"'"
        if (searchTitle != ""):
            if (searchDate != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " title LIKE '%" + searchTitle.upper() + "%'"
        if filterA == "future_only":
            page = 1
            if (searchStr == ""):
                searchStr = " WHERE "  
            else:
                searchStr = searchStr + " AND "   
            searchStr = searchStr + " date >= '" + today.strftime("%Y-%m-%d") + "'"
        print("Ecco la searchStr dopo la post: " + searchStr)
        session["team_filter"] = searchStr

        cursor.execute(
            'SELECT COUNT(*) AS count FROM team ' + searchStr
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']  

    offset = (int(page)-1) * per_page
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    print(str(per_page) + " ----- " + str(offset))
    #print("searchStr: "+searchStr)
    query = ('SELECT id, title, DATE_FORMAT(date,"%d/%m/%y") as data'
            ' FROM team ')
    searchStr = session["team_filter"]
    query = query + searchStr + ' ORDER BY date DESC LIMIT %s OFFSET %s'
    cursor.execute(query,(per_page, offset))
    teams = cursor.fetchall()
    
    return render_template('team/index.html', teams=teams, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr, filterA=filterA)

@bp.route('/team/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    anag_people_ld = get_anag_people() #lista dizionari
    anag_people = json.dumps(anag_people_ld) #json
    anag_tool_ld = get_anag_tool() #lista dizionari
    anag_tools = json.dumps(anag_tool_ld) #json
    anag_tool_type_ld = get_anag_tool_type() #lista dizionari
    anag_tool_type = json.dumps(anag_tool_type_ld) #json
    anag_acts_ld = get_actListFiltered(date) #lista dizionari
    anag_acts = json.dumps(anag_acts_ld) #json

    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']

        dati_jsGridPeople_stringa = request.form.get('dati_jsGridPeople_json')
        dati_jsGridPeople = []
        if dati_jsGridPeople_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridPeople = json.loads(dati_jsGridPeople_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridTool_stringa = request.form.get('dati_jsGridTool_json')
        dati_jsGridTool = []
        if dati_jsGridTool_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridTool = json.loads(dati_jsGridTool_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridAct_stringa = request.form.get('dati_jsGridAct_json')
        dati_jsGridAct = []
        if dati_jsGridAct_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridAct = json.loads(dati_jsGridAct_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        error = None

        if (not date) or (not title):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            #Creo il nuovo record per la squadra
            cursor.execute(
                'INSERT INTO team (title, date, start_time, finish_time, notes) '
                ' VALUES (%s, %s, %s, %s, %s)',
                (title, date, start_time, finish_time, notes)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            id = row['last_insert']

            for record in dati_jsGridPeople:
                # 'record' è ora un singolo dizionario 
                # Estraggo i singoli campi da questo dizionario
                people_id = record['id']
                cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                    ' VALUES (%s, %s)',
                    (id, people_id))
                db.commit()
            
            for record in dati_jsGridTool:
                tool_id = record['tool_id']
                cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                    ' VALUES (%s, %s)',
                    (id, tool_id))
                db.commit()
            
            for record in dati_jsGridAct:
                act_id = record['act_id']
                cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                    ' VALUES (%s, %s)',
                    (id, act_id))
                db.commit()

            return redirect(url_for('team.index'))

    return render_template('team/create.html', anag_people=anag_people, anag_tools=anag_tools, anag_tool_type=anag_tool_type, anag_acts=anag_acts)

@bp.route('/team/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    date = sel_date
    anag_people_ld = get_anag_people() #lista dizionari
    anag_people = json.dumps(anag_people_ld) #json
    anag_tool_ld = get_anag_tool() #lista dizionari
    anag_tools = json.dumps(anag_tool_ld) #json
    anag_tool_type_ld = get_anag_tool_type() #lista dizionari
    anag_tool_type = json.dumps(anag_tool_type_ld) #json
    anag_acts_ld = get_actListFiltered(date) #lista dizionari
    anag_acts = json.dumps(anag_acts_ld) #json

    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        dati_jsGridPeople_stringa = request.form.get('dati_jsGridPeople_json')
        dati_jsGridPeople = []
        if dati_jsGridPeople_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridPeople = json.loads(dati_jsGridPeople_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridTool_stringa = request.form.get('dati_jsGridTool_json')
        dati_jsGridTool = []
        if dati_jsGridTool_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridTool = json.loads(dati_jsGridTool_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridAct_stringa = request.form.get('dati_jsGridAct_json')
        dati_jsGridAct = []
        if dati_jsGridAct_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridAct = json.loads(dati_jsGridAct_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        error = None

        if (not date) or (not title):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            #Creo il nuovo record per la squadra
            cursor.execute(
                'INSERT INTO team (title, date, start_time, finish_time, notes) '
                ' VALUES (%s, %s, %s, %s, %s)',
                (title, date, start_time, finish_time, notes)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            id = row['last_insert']

            for record in dati_jsGridPeople:
                # 'record' è ora un singolo dizionario 
                # Estraggo i singoli campi da questo dizionario
                people_id = record['id']
                cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                    ' VALUES (%s, %s)',
                    (id, people_id))
                db.commit()
            
            for record in dati_jsGridTool:
                tool_id = record['tool_id']
                cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                    ' VALUES (%s, %s)',
                    (id, tool_id))
                db.commit()
            
            for record in dati_jsGridAct:
                act_id = record['act_id']
                cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                    ' VALUES (%s, %s)',
                    (id, act_id))
                db.commit()

            return redirect(url_for('cal_team_planned.show_cal'))

    return render_template('team/create_from_cal.html',anag_people=anag_people, anag_tools=anag_tools, anag_tool_type=anag_tool_type, anag_acts=anag_acts,sel_date=sel_date)

@bp.route('/team/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    team = get_team(id)
    date = team['date']
    people_ld = get_teamPeople(id)
    people = json.dumps(people_ld) #json
    tools_ld = get_teamTool(id)
    tools = json.dumps(tools_ld) #json
    acts_ld = get_teamAct(id)
    acts = json.dumps(acts_ld) #json
    anag_people_ld = get_anag_people() #lista dizionari
    anag_people = json.dumps(anag_people_ld) #json
    anag_tool_ld = get_anag_tool() #lista dizionari
    anag_tools = json.dumps(anag_tool_ld) #json
    anag_tool_type_ld = get_anag_tool_type() #lista dizionari
    anag_tool_type = json.dumps(anag_tool_type_ld) #json
    anag_acts_ld = get_actListFiltered(date) #lista dizionari
    anag_acts = json.dumps(anag_acts_ld) #json
    
    if request.method == 'POST': 
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        
        dati_jsGridPeople_stringa = request.form.get('dati_jsGridPeople_json')
        dati_jsGridPeople = []
        if dati_jsGridPeople_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridPeople = json.loads(dati_jsGridPeople_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridTool_stringa = request.form.get('dati_jsGridTool_json')
        dati_jsGridTool = []
        if dati_jsGridTool_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridTool = json.loads(dati_jsGridTool_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridAct_stringa = request.form.get('dati_jsGridAct_json')
        dati_jsGridAct = []
        if dati_jsGridAct_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridAct = json.loads(dati_jsGridAct_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        error = None

        if (not title) or (not date):
            error = 'Compila tutti i campi obbligatori.'
            
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE team SET title = %s, date = %s, start_time = %s, finish_time = %s, notes = %s '
                ' WHERE id = %s',
                (title, date, start_time, finish_time, notes, id)
            )
            db.commit()
            cursor.execute('DELETE FROM rel_team_people WHERE team_id = %s', (id,))
            db.commit()
            for record in dati_jsGridPeople:
                print(record)
                people_id = record['id']
                cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                    ' VALUES (%s, %s)',
                    (id, people_id))
                db.commit()
            cursor.execute('DELETE FROM rel_team_tool WHERE team_id = %s', (id,))
            db.commit()
            for record in dati_jsGridTool:
                tool_id = record['tool_id']
                cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                    ' VALUES (%s, %s)',
                    (id, tool_id))
            db.commit()
            
            cursor.execute('DELETE FROM rel_team_activity WHERE team_id = %s', (id,))
            db.commit()
            for record in dati_jsGridAct:
                act_id = record['act_id']
                cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                    ' VALUES (%s, %s)',
                    (id, act_id))
            db.commit()

            return redirect(url_for('team.index'))
    show_calendar =  session["show_calendar"]
    return render_template('team/update.html', team=team, people=people, anag_people=anag_people, tools=tools, anag_tools=anag_tools, anag_tool_type=anag_tool_type, acts=acts, anag_acts=anag_acts, show_calendar=show_calendar)

@bp.route('/team/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    team = get_team(id)
    people_ld = get_teamPeople(id)
    people = json.dumps(people_ld) #json
    tools_ld = get_teamTool(id)
    tools = json.dumps(tools_ld) #json
    #acts_ld = get_teamAct(id)
    #acts = json.dumps(acts_ld) #json
    anag_people_ld = get_anag_people() #lista dizionari
    anag_people = json.dumps(anag_people_ld) #json
    anag_tool_ld = get_anag_tool() #lista dizionari
    anag_tools = json.dumps(anag_tool_ld) #json
    anag_tool_type_ld = get_anag_tool_type() #lista dizionari
    anag_tool_type = json.dumps(anag_tool_type_ld) #json
    #anag_acts_ld = get_actListFiltered(date) #lista dizionari
    #anag_acts = json.dumps(anag_acts_ld) #json
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        dati_jsGridPeople_stringa = request.form.get('dati_jsGridPeople_json')
        dati_jsGridPeople = []
        if dati_jsGridPeople_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridPeople = json.loads(dati_jsGridPeople_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridTool_stringa = request.form.get('dati_jsGridTool_json')
        dati_jsGridTool = []
        if dati_jsGridTool_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridTool = json.loads(dati_jsGridTool_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        dati_jsGridAct_stringa = request.form.get('dati_jsGridAct_json')
        dati_jsGridAct = []
        if dati_jsGridAct_stringa:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_jsGridAct = json.loads(dati_jsGridAct_stringa)
                #print(dati_griglia)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia")
                error = 'Errore nella decodifica dei dati JSON della griglia.'

        error = None

        if (not title) or (not date):
            error = 'Compila tutti i campi obbligatori.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO team (title, date, start_time, finish_time, notes) '
                ' VALUES (%s, %s, %s, %s, %s)',
                (title, date, start_time, finish_time, notes)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            id = row['last_insert']

            for record in dati_jsGridPeople:
                # 'record' è ora un singolo dizionario 
                # Estraggo i singoli campi da questo dizionario
                people_id = record['id']
                cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                    ' VALUES (%s, %s)',
                    (id, people_id))
                db.commit()
            
            for record in dati_jsGridTool:
                tool_id = record['tool_id']
                cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                    ' VALUES (%s, %s)',
                    (id, tool_id))
                db.commit()
            
            for record in dati_jsGridAct:
                print("record:")
                print(record)
                act_id = record['act_id']
                cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                    ' VALUES (%s, %s)',
                    (id, act_id))
                db.commit()


            return redirect(url_for('team.index'))
    return render_template('team/duplicate.html', team=team, people=people, anag_people=anag_people, tools=tools, anag_tools=anag_tools, anag_tool_type=anag_tool_type)


@bp.route('/team/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM rel_team_people WHERE team_id = %s', (id,))
    cursor.execute('DELETE FROM rel_team_tool WHERE team_id = %s', (id,))
    cursor.execute('DELETE FROM rel_team_activity WHERE team_id = %s', (id,))
    cursor.execute('DELETE FROM team WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('team.index'))


@bp.route('/team/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    team = get_team(id)
    date = team['date']
    people_ld = get_teamPeople(id)
    people = json.dumps(people_ld) #json
    #print("people:")
    #print(people)
    tools_ld = get_teamTool(id)
    tools = json.dumps(tools_ld) #json
    print("tools:")
    print(tools)
    acts_ld = get_teamAct(id)
    acts = json.dumps(acts_ld) #json
    print("acts:")
    print(acts)
    anag_people_ld = get_anag_people() #lista dizionari
    anag_people = json.dumps(anag_people_ld) #json
    anag_tool_ld = get_anag_tool() #lista dizionari
    anag_tools = json.dumps(anag_tool_ld) #json
    print("anag_tools")
    print(anag_tools)
    anag_tool_type_ld = get_anag_tool_type() #lista dizionari
    anag_tool_type = json.dumps(anag_tool_type_ld) #json
    anag_acts_ld = get_actListFiltered(date) #lista dizionari
    anag_acts = json.dumps(anag_acts_ld) #json
    show_calendar =  session["show_calendar"]
    return render_template('team/detail.html', team=team, people=people, anag_people=anag_people, tools=tools, anag_tools=anag_tools, anag_tool_type=anag_tool_type, acts=acts, anag_acts=anag_acts, show_calendar=show_calendar)

@bp.route("/team_sel_acts/<date>", methods=('POST',))
@login_required
def team_sel_acts(date):
    anag_act = get_actListFiltered(date)
    return (anag_act)

def get_team(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    #Uso CAST e SUBTRING per ottenere il formato stringa HH:MM, 
    # altrimenti il connettore SQL tira fuori un tipo timedelta.
    cursor.execute(
        'SELECT id, title, date, SUBSTRING(CAST(start_time AS CHAR),1,5) as start_time, SUBSTRING(CAST(finish_time AS CHAR),1,5) as finish_time, notes ' 
        ' FROM team'
        ' WHERE id = %s',
        (id,)
    )
    team = cursor.fetchone()
    if team is None:
        abort(404, f"team id {id} non esiste.")

    return team

def get_anag_people():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(surname," ",name) AS name FROM people WHERE cessato=0'
    )
    anag_people=cursor.fetchall()
    return anag_people

def get_anag_tool():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT t.id AS tool_id, CONCAT(t.brand," ",t.model," ",t.license_plate) AS name, tt.id AS type_id, tt.type AS type ' 
        ' FROM tool t'
        ' INNER JOIN tool_type tt on  t.tool_type_id = tt.id'
        ' WHERE discontinued=0 and tt.code IN ("AUTOC","TRATT","RIMOR","RIGRU","FURGO","PLE","RASAS","ESCAV")'
    )
    anag_tool=cursor.fetchall()
    return anag_tool

def get_anag_tool_type():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT tt.id AS type_id, tt.type ' 
        ' FROM tool_type tt'
        ' WHERE tt.code IN ("AUTOC","TRATT","RIMOR","RIGRU","FURGO","PLE","RASAS","ESCAV")'
    )
    anag_tool_type=cursor.fetchall()
    return anag_tool_type

def get_teamPeople(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'SELECT p.id AS id, CONCAT(p.surname," ",p.name) AS name ' 
       ' FROM rel_team_people r' 
        ' INNER JOIN people p ON r.people_id = p.id'
        ' WHERE r.team_id = %s', (id,)
    )
    people=cursor.fetchall()
    return people

def get_teamTool(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'SELECT t.id AS tool_id, CONCAT(t.brand," ",t.model, " ",t.license_plate) AS name, tt.id AS type_id, tt.type AS type '
       ' FROM rel_team_tool r' 
       ' INNER JOIN tool t ON r.tool_id = t.id'
       ' INNER JOIN tool_type tt on t.tool_type_id = tt.id '
       ' WHERE r.team_id = %s', (id,)
    )
    tool=cursor.fetchall()
    return tool

def get_teamAct(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'select a.id AS act_id, CONCAT(c.full_name, " - ", c.city, " - ", a.title) AS act_desc  ' 
       ' FROM rel_team_activity r' 
       ' INNER JOIN activity a ON r.activity_id = a.id'
       ' inner join p_order o on o.id = a.p_order_id '
       ' inner join customer c on c.id = o.customer_id ' 
       ' WHERE r.team_id = %s', (id,)
    )
    act=cursor.fetchall()
    return act

def get_actListFiltered(date):
    #Con questa query si ottengono solo le attività che comprendono la data della squadra
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'select a.id AS act_id, CONCAT(c.full_name, " - ", c.city, " - ", a.title) AS act_desc '
        ' from activity a '
        ' inner join p_order o on o.id = a.p_order_id '
        ' inner join customer c on c.id = o.customer_id ' 
        ' WHERE %s >= a.start AND %s <= a.end '
        ' ORDER BY c.full_name ASC',
        (date,date)
    )
    anag_act = cursor.fetchall()
    if anag_act is None:
        abort(404, f"anag_acts è vuota.")
    return anag_act
