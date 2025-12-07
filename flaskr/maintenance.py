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

bp = Blueprint('maintenance', __name__)

@bp.route('/maintenance', methods=('GET', 'POST'))
@login_required
def index():
    session["show_calendar"] = 'N'
    if not "maintenance_filter" in session:
        searchStr = ""
    else:
        searchStr = session["maintenance_filter"]
        current_app.logger.debug("1 - maintenance_filter: " + session["maintenance_filter"])
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT m.id, m.description, m.start AS start, m.end AS end, CONCAT(t.brand," - ",t.model) AS tool_name, tt.type '
             ' FROM maintenance m'
             ' INNER JOIN tool t ON m.tool_id = t.id '
			 ' INNER JOIN tool_type tt ON t.tool_type_id = tt.id ' +
            searchStr + ") AS maintenances"
            )
    
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')

    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 
        current_app.logger.debug("Sono nella POST")
        searchDate = request.form['searchDate']
        searchTool = request.form['searchTool']
        searchType = request.form['searchType']
        current_app.logger.debug("searchDate: " + searchDate)
        current_app.logger.debug("searchTool: " + searchTool)
        current_app.logger.debug("searchType: " + searchType)
        if ((searchDate + searchTool + searchType) != ""):
            searchStr = " WHERE "
        else:
            searchStr = ""
        if (searchDate != ""):
            searchStr = searchStr + "start = '" + searchDate +"'"
        if (searchTool != ""):
            if (searchDate != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " CONCAT(t.brand,' - ',t.model) LIKE '%" + searchTool.upper() + "%'"
        if (searchType != ""):
            if (searchDate != "" or searchTool != ""):
                searchStr = searchStr + " AND "
            searchStr = searchStr + " tt.type LIKE '%" + searchType.upper() + "%'"
        #searchStr = searchStr.upper()
        current_app.logger.debug("searchStr: " + searchStr)
        #print("searchStr: " + searchStr)
        session["maintenance_filter"] = searchStr

        cursor.execute(
            'SELECT COUNT(*) AS count FROM '
            ' (SELECT m.id, m.description, m.start AS start, m.end AS end, CONCAT(t.brand," - ",t.model) AS tool_name, tt.type '
             ' FROM maintenance m'
             ' INNER JOIN tool t ON m.tool_id = t.id '
			 ' INNER JOIN tool_type tt ON t.tool_type_id = tt.id ' +
            searchStr + ") AS maintenances"
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    current_app.logger.debug("total: " + str(total))  
    print("maintenance_first_page: " + session["maintenance_first_page"])  
    if session["maintenance_first_page"] == 'N':
        if page == None:
            page = 1
        offset = (int(page)-1) * per_page
    else:
        #Pagina iniziale (session["maintenance_first_page"] == 'Y')
        #Individuo la pagina più vicina alla data odierna
        today = date.today()
        query = ('SELECT COUNT(*) AS count FROM '
            ' (SELECT m.id, m.description, m.start AS start, m.end AS end, CONCAT(t.brand," - ",t.model) AS tool_name '
            ' FROM maintenance m'
            ' INNER JOIN tool t ON m.tool_id = t.id '
			' INNER JOIN tool_type tt ON t.tool_type_id = tt.id ')
        if searchStr == "":
            query = query + ' WHERE start < %s) AS maintenances'
        else:
            query = query + searchStr +  ' AND start < %s) AS maintenances'
        print(query)
        cursor.execute(query,(today,))
        rowCount = cursor.fetchone()
        number_to_bypass = rowCount['count']   
        page_num = int((number_to_bypass / per_page)) + 1 
        print ("page_num: " + str(page_num))
        offset = (int(page_num)-1) * per_page
        page = str(page_num) 
        session["maintenance_first_page"] = 'N'
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    print(str(per_page) + " ----- " + str(offset))
    cursor.execute(
            'SELECT m.id, m.description, DATE_FORMAT(m.start,"%d/%m/%y") AS start, DATE_FORMAT(m.end,"%d/%m/%y") AS end, CONCAT(t.brand," - ",t.model) AS tool_name, tt.type, '
            ' m.done, m.extra, tt.type, tt.asset, tt.inail '
            ' FROM maintenance m'
            ' INNER JOIN tool t ON m.tool_id = t.id '
			' INNER JOIN tool_type tt ON t.tool_type_id = tt.id ' 
             +
            searchStr +
            ' ORDER BY m.start ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
    maintenances = cursor.fetchall()
    
    return render_template('maintenance/index.html', maintenances=maintenances, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/maintenance/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
    anag_tool = get_anag_tool()
    if request.method == 'POST':
        description = request.form['description']
        start = request.form['start']
        end = request.form['end']
        tool_id = request.form['input_tool_id']
        notes = request.form['notes']
        extra = request.form['extra']
        done = "0"
        file = request.files['file']
        file_name = request.files['file'].filename
        file_content = file.read()
       
        error = None
        if (not start) or (not end) or (not tool_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Creo il nuovo record per la manutenzione
            cursor.execute(
                'INSERT INTO maintenance (description, start, end, tool_id, notes, extra, done, file_name, file_content)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (description, start, end, tool_id, notes, extra, done, file_name, file_content)
            )
            db.commit()
            return redirect(url_for('maintenance.index'))

    return render_template('maintenance/create.html', anag_tool=anag_tool)

@bp.route('/maintenance/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
    anag_tool = get_anag_tool()
    if request.method == 'POST':
        description = request.form['description']
        start = request.form['start']
        end = request.form['end']
        tool_id = request.form['input_tool_id']
        notes = request.form['notes']
        extra = request.form['extra']
        done = "0"
    
        error = None

        if (not start) or (not end) or (not tool_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Creo il nuovo record per la manutenzione
            cursor.execute(
                'INSERT INTO maintenance (description, start, end, tool_id, notes, extra, done)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (description, start, end, tool_id, notes, extra, done)
            )
            db.commit()
            
            return redirect(url_for('cal_maintenance.show_cal'))

    return render_template('maintenance/create_from_cal.html', anag_tool=anag_tool, sel_date=sel_date)

@bp.route('/maintenance/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
    current_app.logger.debug("id: " + str(id))
    maintenance = get_maintenance(id)
    anag_tool = get_anag_tool()
    show_calendar = session["show_calendar"]
    if request.method == 'POST':
        description = request.form['description']
        start = request.form['start']
        end = request.form['end']
        tool_id = request.form['input_tool_id']
        notes = request.form['notes']
        extra = request.form['extra']
        file = request.files['file']
        file_name = request.files['file'].filename
        file_content = file.read()
        error = None

        if (not start) or (not end) or (not tool_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE maintenance SET description = %s, start = %s, end = %s, tool_id = %s, notes = %s, extra = %s, file_name = %s, file_content = %s'
                ' WHERE id = %s',
               (description, start, end, tool_id, notes, extra,file_name, file_content, id)
            )
            db.commit()
            if show_calendar == "Y":
                 return redirect(url_for('cal_maintenance.show_cal'))
            else:
                return redirect(url_for('maintenance.index'))
    return render_template('maintenance/update.html', maintenance=maintenance, anag_tool=anag_tool, show_calendar=show_calendar)

@bp.route('/maintenance/<int:id>/download_file', methods=('POST',))
@login_required
def download_file(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
        
    maintenance = get_maintenance(id)
    show_calendar = session["show_calendar"]
    error = None

    if (not maintenance['file_name']):
        error = 'Non esiste la fattura allegata.'

    if error is not None:
        flash(error)
        if show_calendar == "Y":
            return redirect(url_for('cal_maintenance.show_cal'))
        else:
            return redirect(url_for('maintenance.index'))
    else:
        return send_file(BytesIO(maintenance['file_content']), download_name=maintenance['file_name'], as_attachment=True )

@bp.route('/maintenance/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
    current_app.logger.debug("id: " + str(id))
    maintenance = get_maintenance(id)
    anag_tool = get_anag_tool()
        
    if request.method == 'POST':
        description = request.form['description']
        start = request.form['start']
        end = request.form['end']
        tool_id = request.form['input_tool_id']
        notes = request.form['notes']
        extra = request.form['extra']
        done = "0"
        file = request.files['file']
        file_name = request.files['file'].filename
        file_content = file.read()
        error = None

        if (not start) or (not end) or (not tool_id) or (not description):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO maintenance (description, start, end, tool_id, notes, extra, done, file_name, file_content)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (description, start, end, tool_id, notes, extra, done, file_name, file_content)
            )
            db.commit()
           
            return redirect(url_for('maintenance.index'))
    current_app.logger.debug("Sto per fare la return da duplicate")
    return render_template('maintenance/duplicate.html', maintenance=maintenance, anag_tool=anag_tool)

@bp.route('/maintenance/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("maintenance.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM maintenance WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('maintenance.index'))


@bp.route('/maintenance/<int:id>/detail', methods=('GET','POST'))
@login_required
def detail(id): 
    maintenance = get_maintenance(id) 
    show_calendar = session["show_calendar"]
    if request.method == 'POST':
        if g.role != "ADMIN":
            error = 'Non sei autorizzato a questa funzione.'
            flash(error)
            return redirect(url_for("maintenance.index"))
        error = None
        if (not maintenance['file_name']):
            error = 'Non esiste la fattura allegata.'

            if error is not None:
                print("Sono qui!")
                flash(error)
                return render_template('maintenance/detail.html', maintenance=maintenance, show_calendar=show_calendar)
            else:
                return send_file(BytesIO(maintenance['file_content']), download_name=maintenance['file_name'], as_attachment=True )    
        
    return render_template('maintenance/detail.html', maintenance=maintenance, show_calendar=show_calendar)    

@bp.route('/maintenance/<int:id>/to_do', methods=('POST',))
@login_required
def to_do(id):
    current_app.logger.debug("to_do dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE maintenance SET done = False'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "to_do"

@bp.route('/maintenance/<int:id>/done', methods=('POST',))
@login_required
def done(id):
    current_app.logger.debug("done dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE maintenance SET done = True'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "done"


def get_maintenance(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT m.id, m.description, m.start, m.end, m.done, m.extra, m.notes, '
        ' CONCAT(t.brand," - ",t.model) AS tool_name, m.tool_id AS tool_id, m.file_name, m.file_content '
        ' FROM maintenance m INNER JOIN tool t ON m.tool_id = t.id '
        ' WHERE m.id = %s',
        (id,)
    )
    maintenance = cursor.fetchone()
    if maintenance is None:
        abort(404, f"maintenance id {id} non esiste.")
    print("get_maintenance:")
    #print(maintenance)
    return maintenance

    if siteList is None:
        abort(404, f"siteList è vuota.")
    current_app.logger.debug(siteList)
    return siteList

def get_anag_tool_type():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(id order by type) AS id, GROUP_CONCAT(type) AS type FROM tool_type'
    )
    anag_tool_type=cursor.fetchone()
    return anag_tool_type

def get_anag_tool():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tool_id, CONCAT(brand," ",model," ",license_plate," ",serial_number) AS tool_name FROM tool  ORDER BY tool_name'
    )
    anag_tool=cursor.fetchall()
    return anag_tool
