from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('tool', __name__)

@bp.route('/tool', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM tool')
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    searchStr = ""
    if request.method == 'POST': 
        searchStr = request.form['search']
        searchQ = "%" + searchStr + "%"
        searchQ = searchQ.upper()
        cursor.execute(
            'SELECT COUNT(*) AS count FROM tool t INNER JOIN tool_type tt ON t.tool_type_id = tt.id WHERE CONCAT(brand, " ",model, " ", license_plate, " ", serial_number) LIKE %s',
            (searchQ,)
            )
        rowCount = cursor.fetchone()
        total = rowCount['count']
    if page != None:
        offset = (int(page)-1) * per_page
    else:
        page = "1"
        offset = 0   
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    
    if searchStr == "":
        cursor.execute(
            'SELECT t.id, CONCAT(brand, " ",model, " ", license_plate, " ", serial_number) AS tool_name, tt.type, tt.inail, tt.asset, t.discontinued '
            ' FROM tool t INNER JOIN tool_type tt ON t.tool_type_id = tt.id '
            ' ORDER BY tool_name ASC LIMIT %s OFFSET %s',
            (per_page, offset)
        )
        tools = cursor.fetchall()
    else:
        searchQ = "%" + searchStr + "%"
        searchQ = searchQ.upper()
        cursor.execute(
            'SELECT t.id, CONCAT(brand, " ",model, " ", license_plate, " ", serial_number) AS tool_name, tt.type, tt.inail, tt.asset, t.discontinued '
            ' FROM tool t INNER JOIN tool_type tt ON t.tool_type_id = tt.id '
            ' WHERE CONCAT(brand, " ",model, " ", license_plate, " ", serial_number) LIKE %s'
            ' ORDER BY tool_name ASC LIMIT %s OFFSET %s',
            (searchQ, per_page, offset)
        )
        tools = cursor.fetchall()
    return render_template('tool/index.html', tools=tools, page=page,
                           per_page=per_page,pagination=pagination, search=searchStr)

@bp.route('/tool/create', methods=('GET', 'POST'))
@login_required
def create():
    tool_typeList = get_tool_typeList()
    if request.method == 'POST':
        tool_type_id = request.form['input_tool_type_id']
        brand = request.form['brand']
        model = request.form['model']
        serial_number = request.form['serial_number']
        license_plate = request.form['license_plate']
        notes = request.form['notes']
        error = None

        if (not tool_type_id) or (not brand) or (not model):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO tool (tool_type_id, brand, model, serial_number, license_plate, notes)'
                ' VALUES (%s, %s, %s, %s, %s, %s)',
                (tool_type_id, brand, model, serial_number, license_plate, notes)
            )
            db.commit()
            return redirect(url_for('tool.index'))

    return render_template('tool/create.html', tool_typeList=tool_typeList)

@bp.route('/tool/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    tool = get_tool(id)
    tool_typeList = get_tool_typeList()
    
    if request.method == 'POST':
        tool_type_id = request.form['input_tool_type_id']
        brand = request.form['brand']
        model = request.form['model']
        serial_number = request.form['serial_number']
        license_plate = request.form['license_plate']
        notes = request.form['notes']
        discontinued = request.form['discontinued'] 
        error = None

        if (not tool_type_id) or (not brand) or (not model):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE tool SET tool_type_id = %s, brand = %s, model = %s, serial_number = %s, '
                ' license_plate = %s, notes = %s, discontinued = %s'
                ' WHERE id = %s',
                (tool_type_id, brand, model, serial_number, license_plate, notes, discontinued, id)
            )
            db.commit()
            return redirect(url_for('tool.index'))
    return render_template('tool/update.html', tool=tool, tool_typeList=tool_typeList)

@bp.route('/tool/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM tool WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('tool.index'))

@bp.route('/tool/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    tool = get_tool(id)
    tool_typeList = get_tool_typeList()
    return render_template('tool/detail.html', tool=tool, tool_typeList=tool_typeList)

def get_tool(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, tool_type_id, brand, model, serial_number, license_plate, notes, discontinued' 
        ' FROM tool'
        ' WHERE id = %s',
        (id,)
    )
    tool = cursor.fetchone()

    if tool is None:
        abort(404, f"tool id {id} non esiste.")
    
    """if site['contact_people'] == None:
        site['contact_people'] = ""
    if site['telephone'] == None:
        site['telephone'] = ""
    if site['email'] == None:
        site['email'] = ""  """

    return tool

def get_tool_typeList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, type'
        ' FROM tool_type ORDER BY type ASC'
    )
    tool_typeList=cursor.fetchall()

    if tool_typeList is None:
        abort(404, f"tool_typeList è vuota.")
    return tool_typeList
