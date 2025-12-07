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
    
    anag_people = get_anag_people()
    anag_tool = get_anag_tool()
    #date = datetime.today().strftime('%Y-%m-%d')
    date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    anag_acts = get_actListFiltered(date)
    anag_act_ids = anag_acts["act_id"]
    anag_act_descs = anag_acts["act_desc"]
    if anag_act_ids == None:
        anag_act_ids = ""
        anag_act_descs = ""

    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        people_ids = request.form['people_ids']
        tool_ids = request.form['tool_ids']
        act_ids = request.form['act_ids']

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
            people_ids_arr = people_ids.split(",")
            i=0
            if (len(people_ids_arr) > 0 and people_ids_arr[0] != ""):
                for people_id in people_ids_arr:
                    cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                        ' VALUES (%s, %s)',
                        (id, people_id))
                    i = i+1
                db.commit()

            tool_ids_arr = tool_ids.split(",")
            i=0
            if (len(tool_ids_arr) > 0 and tool_ids_arr[0] != ""):
                print("i="+str(i))
                for tool_id in tool_ids_arr:
                    cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                        ' VALUES (%s, %s)',
                        (id, tool_id))
                    i = i+1
                db.commit()

            act_ids_arr = act_ids.split(",")
            i=0
            if (len(act_ids_arr) > 0 and act_ids_arr[0] != ""):
                print("i="+str(i))
                for act_id in act_ids_arr:
                    cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                        ' VALUES (%s, %s)',
                        (id, act_id))
                    i = i+1
                db.commit()

            return redirect(url_for('team.index'))

    return render_template('team/create.html', anag_people=anag_people, anag_tool=anag_tool, anag_act_ids=anag_act_ids, anag_act_descs=anag_act_descs)

@bp.route('/team/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    
    anag_people = get_anag_people()
    anag_tool = get_anag_tool()
    #date = datetime.today().strftime('%Y-%m-%d')
    date = sel_date
    anag_acts = get_actListFiltered(date)
    anag_act_ids = anag_acts["act_id"]
    anag_act_descs = anag_acts["act_desc"]
    if anag_act_ids == None:
        anag_act_ids = ""
        anag_act_descs = ""

    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        people_ids = request.form['people_ids']
        tool_ids = request.form['tool_ids']
        act_ids = request.form['act_ids']

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
            people_ids_arr = people_ids.split(",")
            i=0
            if (len(people_ids_arr) > 0 and people_ids_arr[0] != ""):
                for people_id in people_ids_arr:
                    cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                        ' VALUES (%s, %s)',
                        (id, people_id))
                    i = i+1
                db.commit()

            tool_ids_arr = tool_ids.split(",")
            i=0
            if (len(tool_ids_arr) > 0 and tool_ids_arr[0] != ""):
                print("i="+str(i))
                for tool_id in tool_ids_arr:
                    cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                        ' VALUES (%s, %s)',
                        (id, tool_id))
                    i = i+1
                db.commit()

            act_ids_arr = act_ids.split(",")
            i=0
            if (len(act_ids_arr) > 0 and act_ids_arr[0] != ""):
                print("i="+str(i))
                for act_id in act_ids_arr:
                    cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                        ' VALUES (%s, %s)',
                        (id, act_id))
                    i = i+1
                db.commit()

            return redirect(url_for('cal_team_planned.show_cal'))

    return render_template('team/create_from_cal.html',anag_people=anag_people, anag_tool=anag_tool, anag_act_ids=anag_act_ids, anag_act_descs=anag_act_descs,sel_date=sel_date)

@bp.route('/team/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    team = get_team(id)
    date = team['date']
    #start_time = team['start_time']
    ret_peoples = get_teamPeople_ids(id)
    people = ret_peoples[0]
    people_ids = people['id']
    people_names = people['name']
    ret_tools = get_teamTool_ids(id)
    tool = ret_tools[0]
    tool_ids = tool['id']
    tool_names = tool['name']
    ret_acts = get_teamAct_ids(id)
    act = ret_acts[0]
    act_ids = act['act_id']
    act_descs = act['act_desc']
    anag_people = get_anag_people()
    anag_tool = get_anag_tool()
    anag_acts = get_actListFiltered(date)
    anag_act_ids = anag_acts["act_id"]
    anag_act_descs = anag_acts["act_desc"]
    if anag_act_ids == None:
        anag_act_ids = ""
        anag_act_descs = ""
    
    if request.method == 'POST': 
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        people_ids = request.form['people_ids']
        tool_ids = request.form['tool_ids']
        act_ids = request.form['act_ids']
        people_ids_arr = people_ids.split(",")
        tool_ids_arr = tool_ids.split(",")
        act_ids_arr = act_ids.split(",")
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
            i=0
            if (len(people_ids_arr) > 0 and people_ids_arr[0] != ""):
                for people_id in people_ids_arr:
                    cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                        ' VALUES (%s, %s)',
                        (id, people_id))
                    i = i+1
                db.commit()
            cursor.execute('DELETE FROM rel_team_tool WHERE team_id = %s', (id,))
            db.commit()
            i=0
            if (len(tool_ids_arr) > 0 and tool_ids_arr[0] != ""):
                for tool_id in tool_ids_arr:
                    cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                        ' VALUES (%s, %s)',
                        (id, tool_id))
                    i = i+1
                db.commit()
            
            cursor.execute('DELETE FROM rel_team_activity WHERE team_id = %s', (id,))
            db.commit()
            i=0
            if (len(act_ids_arr) > 0 and act_ids_arr[0] != ""):
                for act_id in act_ids_arr:
                    cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                        ' VALUES (%s, %s)',
                        (id, act_id))
                    i = i+1
                db.commit()

            return redirect(url_for('team.index'))
    show_calendar =  session["show_calendar"]
    return render_template('team/update.html', team=team, people_ids=people_ids, people_names=people_names, anag_people=anag_people, tool_ids=tool_ids, tool_names=tool_names, anag_tool=anag_tool, anag_act_ids=anag_act_ids, anag_act_descs=anag_act_descs, act_ids=act_ids, act_descs=act_descs,show_calendar=show_calendar)

@bp.route('/team/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("team.index"))
    team = get_team(id)
    ret_peoples = get_teamPeople_ids(id)
    people = ret_peoples[0]
    people_ids = people['id']
    ret_tools = get_teamTool_ids(id)
    tool = ret_tools[0]
    tool_ids = tool['id']
    anag_people = get_anag_people()
    anag_tool = get_anag_tool()
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        start_time = request.form['start_time']
        finish_time = request.form['finish_time']
        notes = request.form['notes']
        people_ids = request.form['people_ids']
        tool_ids = request.form['tool_ids']
        act_ids = request.form['act_ids']
        act_ids_arr = act_ids.split(",")
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
            people_ids_arr = people_ids.split(",")
            i=0
            if (len(people_ids_arr) > 0 and people_ids_arr[0] != ""):
                for people_id in people_ids_arr:
                    cursor.execute('INSERT INTO rel_team_people (team_id, people_id)'
                        ' VALUES (%s, %s)',
                        (id, people_id))
                    i = i+1
                db.commit()

            tool_ids_arr = tool_ids.split(",")
            i=0
            if (len(tool_ids_arr) > 0 and tool_ids_arr[0] != ""):
                print("i="+str(i))
                for tool_id in tool_ids_arr:
                    cursor.execute('INSERT INTO rel_team_tool (team_id, tool_id)'
                        ' VALUES (%s, %s)',
                        (id, tool_id))
                    i = i+1
                db.commit()

            cursor.execute('DELETE FROM rel_team_activity WHERE team_id = %s', (id,))
            db.commit()
            i=0
            if (len(act_ids_arr) > 0 and act_ids_arr[0] != ""):
                for act_id in act_ids_arr:
                    cursor.execute('INSERT INTO rel_team_activity (team_id, activity_id)'
                        ' VALUES (%s, %s)',
                        (id, act_id))
                    i = i+1
                db.commit()

            return redirect(url_for('team.index'))
    return render_template('team/duplicate.html', team=team, people_ids=people_ids, tool_ids=tool_ids, anag_people=anag_people, anag_tool=anag_tool)


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
    ret_peoples = get_teamPeople_ids(id)
    people = ret_peoples[0]
    people_names = people['name']
    ret_tools = get_teamTool_ids(id)
    tool = ret_tools[0]
    tool_names = tool['name']
    ret_acts = get_teamAct_ids(id)
    act = ret_acts[0]
    act_descs = act['act_desc']
    show_calendar =  session["show_calendar"]
    return render_template('team/detail.html', team=team, people_names=people_names, tool_names=tool_names, act_descs=act_descs, show_calendar=show_calendar)

@bp.route("/team_sel_acts/<date>", methods=('POST',))
@login_required
def team_sel_acts(date):
    anag_acts = get_actListFiltered(date)
    #act_ids = anag_acts["act_id"]
    #act_descs = anag_acts["act_desc"]
    return (anag_acts)

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
        'SELECT GROUP_CONCAT(id order by surname,name) AS id, GROUP_CONCAT(CONCAT(surname," ",name) order by surname,name) AS name FROM people WHERE cessato=0'
    )
    anag_people=cursor.fetchone()
    #current_app.logger.debug("get_anag_people")
    #current_app.logger.debug(anag_people)
    return anag_people

def get_anag_tool():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(t.id order by t.brand,t.model) AS id, GROUP_CONCAT(CONCAT(tt.type," ",t.brand," ",t.model," ",t.license_plate) order by t.brand,t.model) AS name ' 
        ' FROM tool t'
        ' INNER JOIN tool_type tt on  t.tool_type_id = tt.id'
        ' WHERE discontinued=0 and tt.type IN ("Autocarro","Trattore","Rimorchio","Rimorchio con gru","Furgone","PLE","Rasaerba semovente","Escavatore")'
        #' WHERE discontinued=0 and tool_type_id IN (10,12,13,14,15,16,17,19)'
    )
    anag_tool=cursor.fetchone()
    print("anag_tool:")
    print(anag_tool)
    return anag_tool

def get_teamPeople_ids(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'SELECT GROUP_CONCAT(p.id) AS id, GROUP_CONCAT(CONCAT(p.surname," ",p.name)) AS name FROM rel_team_people r' 
        ' INNER JOIN people p ON r.people_id = p.id'
        ' WHERE r.team_id = %s', (id,)
    )
    people=cursor.fetchone()
    return [people]

def get_teamTool_ids(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'SELECT GROUP_CONCAT(t.id) AS id, GROUP_CONCAT(CONCAT(t.brand," ",t.model, " ",t.license_plate)) AS name FROM rel_team_tool r' 
        ' INNER JOIN tool t ON r.tool_id = t.id'
        ' WHERE r.team_id = %s', (id,)
    )
    tool=cursor.fetchone()
    return [tool]

def get_teamAct_ids(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
       'select GROUP_CONCAT(a.id) AS act_id, GROUP_CONCAT(CONCAT(c.full_name, " - ", c.city, " - ", a.title) SEPARATOR "|§|") AS act_desc  ' 
       ' FROM rel_team_activity r' 
       ' INNER JOIN activity a ON r.activity_id = a.id'
       ' inner join p_order o on o.id = a.p_order_id '
       ' inner join customer c on c.id = o.customer_id ' 
       ' WHERE r.team_id = %s', (id,)
    )
    act=cursor.fetchone()
    return [act]

def get_actListFiltered(date):
    #Con questa query si ottengono solo le attività che comprendono la data della squadra
    #ma resi come unico record
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'select GROUP_CONCAT(a.id) AS act_id, GROUP_CONCAT(CONCAT(c.full_name, " - ", c.city, " - ", a.title) SEPARATOR "|§|") AS act_desc '
        ' from activity a '
        ' inner join p_order o on o.id = a.p_order_id '
        ' inner join customer c on c.id = o.customer_id ' 
        ' WHERE %s >= a.start AND %s <= a.end '
        ' ORDER BY c.full_name ASC',
        (date,date)
    )
    anag_acts = cursor.fetchone()
    if anag_acts is None:
        abort(404, f"anag_acts è vuota.")
    return anag_acts
