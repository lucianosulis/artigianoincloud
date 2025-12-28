from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('waste_storage', __name__)

@bp.route('/waste_storage', methods=('GET', 'POST'))
@login_required
def index():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    if not "storage_filter" in session:
        session["storage_filter"] = ""
    searchStr = session["storage_filter"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM waste_storage" + searchStr)
    rowCount = cursor.fetchone()
    total = rowCount['count']
    page = request.args.get('page')
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    
    if request.method == 'POST': 
        searchCompany = request.form['searchCompany']
        if searchCompany != "":
            searchStr = " WHERE company_name LIKE '%" + searchCompany.upper() + "%'"
        else:
            searchStr = ""
        current_app.logger.debug("searchStr: " + searchStr)
        session["storage_filter"] = searchStr
        cursor.execute(
            'SELECT COUNT(*) AS count FROM waste_storage ' + searchStr
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
    
    cursor.execute(
        'SELECT * FROM waste_storage ' + searchStr +
        ' ORDER BY company_name ASC '
        ' LIMIT %s OFFSET %s ',
        (per_page, offset)
    )
    waste_storages = cursor.fetchall()
    return render_template('waste_storage/index.html', waste_storages=waste_storages, page=page,
                           per_page=per_page,pagination=pagination)

@bp.route('/waste_storage/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        company_name = request.form['company_name']
        address = request.form['address']
        city = request.form['city']
        zip_code = request.form['zip_code']
        codice_fiscale = request.form['codice_fiscale']
        partita_iva = request.form['partita_iva']
        codice_attivita = request.form['codice_attivita']
        n_autorizzazione = request.form['n_autorizzazione']
        tipo_autorizzazione = request.form['tipo_autorizzazione']

        error = None

        if (not company_name) or (not address) or (not city) or (not codice_fiscale) or (not codice_attivita) or (not n_autorizzazione) or (not tipo_autorizzazione):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO waste_storage (company_name, address, city, zip_code, codice_fiscale, partita_iva,codice_attivita,n_autorizzazione,tipo_autorizzazione)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (company_name, address, city, zip_code, codice_fiscale, partita_iva, codice_attivita, n_autorizzazione, tipo_autorizzazione)
            )
            db.commit()
            return redirect(url_for('waste_storage.index'))

    return render_template('waste_storage/create.html')

@bp.route('/waste_storage/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("waste_storage.index"))
    waste_storage = get_waste_storage(id)
        
    if request.method == 'POST': 
        company_name = request.form['company_name']
        address = request.form['address']
        city = request.form['city']
        zip_code = request.form['zip_code']
        codice_fiscale = request.form['codice_fiscale']
        partita_iva = request.form['partita_iva']
        codice_attivita = request.form['codice_attivita']
        n_autorizzazione = request.form['n_autorizzazione']
        tipo_autorizzazione = request.form['tipo_autorizzazione']
        
        error = None

        if (not company_name) or (not address) or (not city) or (not codice_fiscale) or (not codice_attivita):
            error = 'Compila tutti i campi obbligatori.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE waste_storage SET company_name=%s,address=%s,city=%s,zip_code=%s, ' 
                ' codice_fiscale=%s, partita_iva=%s,'
                ' codice_attivita=%s,n_autorizzazione=%s,tipo_autorizzazione=%s'
                ' WHERE id = %s',
                (company_name, address, city, zip_code, codice_fiscale, partita_iva, codice_attivita, n_autorizzazione, tipo_autorizzazione, id)
            )
            db.commit()
            
            return redirect(url_for('waste_storage.index'))
    return render_template('waste_storage/update.html', waste_storage=waste_storage)

@bp.route('/waste_storage/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    waste_storage = get_waste_storage(id)
    return render_template('waste_storage/detail.html', waste_storage=waste_storage)

@bp.route('/waste_storage/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("waste_storage.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute('DELETE FROM waste_storage WHERE id = %s', (id,))
        db.commit()
    except:
        flash("Errore nella eliminazione del deposito rifiuti. Verifica che non ci siano FIR per questo deposito.")
    return redirect(url_for('waste_storage.index'))

def get_waste_storage(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * ' 
        ' FROM waste_storage'
        ' WHERE id = %s',
        (id,)
    )
    waste_storage = cursor.fetchone()

    if waste_storage is None:
        abort(404, f"waste_storage id {id} non esiste.")
    
    if waste_storage['company_name'] == None:
        waste_storage['city'] = ""
    if waste_storage['address'] == None:
        waste_storage['zip_code'] = ""
    return waste_storage

