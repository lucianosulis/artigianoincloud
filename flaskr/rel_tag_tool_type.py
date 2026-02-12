from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('rel_tag_tool_type', __name__)

@bp.route('/rel_tag_tool_type', methods=('GET','POST'))
@login_required
def index():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM rel_tag_tool_type")
    total = cursor.fetchone()['count']
    #print(f"total: {total}")
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    page = request.args.get('page', 1, type=int)
    offset = (page-1) * per_page 
    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')
    
    cursor.execute(
        'SELECT r.id as id, r.tag_id as tag_id, t.description as tag_description, t.code as tag_code, tt.id as tool_type_id, tt.type as tool_type  '
        ' FROM rel_tag_tool_type r'
        ' INNER JOIN tag t ON r.tag_id=t.id '
        ' INNER JOIN tool_type tt ON r.tool_type_id=tt.id '
        ' ORDER BY t.id ASC '
        ' LIMIT %s OFFSET %s ',
        (per_page, offset)
    )
    rel_tag_tool_types = cursor.fetchall()
    return render_template('rel_tag_tool_type/index.html', rel_tag_tool_types=rel_tag_tool_types, page=page,
                           per_page=per_page,pagination=pagination)

@bp.route('/rel_tag_tool_type/create', methods=('GET', 'POST'))
@login_required
def create():
    tool_type_list = get_tool_typeList()
    tag_list = get_tagList()
    print(f"tag_list: {tag_list}")
    if request.method == 'POST':
        tag_id = request.form.get('tag_id')
        tool_type_id = request.form.get('tool_type_id')
        print(f"tag_id={tag_id} - tool_type_id={tool_type_id}")
        error = None
        if (not tag_id) or (not tool_type_id):
            error = 'Compila tutti i campi obbligatori.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO rel_tag_tool_type (tool_type_id, tag_id)'
                ' VALUES (%s, %s)',
                (tool_type_id, tag_id)
            )
            db.commit()
            return redirect(url_for('rel_tag_tool_type.index'))

    return render_template('rel_tag_tool_type/create.html',tool_type_list=tool_type_list,tag_list=tag_list)

@bp.route('/rel_tag_tool_type/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("rel_tag_tool_type.index"))
    rel_tag_tool_type = get_rel_tag_tool_type(id)
    tool_type_list = get_tool_typeList()
    tag_list = get_tagList()
        
    if request.method == 'POST': 
        tool_type_id = request.form.get('tool_type_id')
        tag_id = request.form.get('tag_id')
        
        error = None

        if (not tool_type_id) or (not tag_id):
            error = 'Compila tutti i campi obbligatori.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE rel_tag_tool_type SET tool_type_id=%s,tag_id=%s ' 
                ' WHERE id = %s',
                (tool_type_id, tag_id, id)
            )
            db.commit()
            
            return redirect(url_for('rel_tag_tool_type.index'))
    return render_template('rel_tag_tool_type/update.html', rel_tag_tool_type=rel_tag_tool_type,tool_type_list=tool_type_list,tag_list=tag_list)

@bp.route('/rel_tag_tool_type/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("rel_tag_tool_type.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('DELETE FROM rel_tag_tool_type WHERE id = %s', (id,))
        db.commit()
    except:
        flash("Errore nella eliminazione della associazione.")
    return redirect(url_for('rel_tag_tool_type.index'))

def get_tagList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, CONCAT(code, " - ", description) as tag'
        ' FROM tag ORDER BY id ASC'
    )
    tag_list=cursor.fetchall()

    if tag_list is None:
        abort(404, f"tagList è vuota.")
    return tag_list

def get_tool_typeList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, type'
        ' FROM tool_type ORDER BY type ASC'
    )
    tool_type_list=cursor.fetchall()

    if tool_type_list is None:
        abort(404, f"tool_typeList è vuota.")
    return tool_type_list

def get_rel_tag_tool_type(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM rel_tag_tool_type '
        ' WHERE id=%s',
        (id,)
    )
    rel_tag_tool_type=cursor.fetchone()
    return rel_tag_tool_type
