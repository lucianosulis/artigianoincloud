from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json,session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flask import Response, render_template
from .geo_utils import geocoordinates
import io

bp = Blueprint('site', __name__)

@bp.route('/site', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("home.index"))
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    search_customer = session.get("site1_search_customer","")
    filterA = session.get("site1_filter","all")

    if request.method == 'GET': 
        page = request.args.get('page', 1, type=int)
        params = session.get("site1_search_params", [])
        searchStr = session.get("site1_search","")
        
    if request.method == 'POST': 
        page = 1
        filterA = request.form.get("filterA","all")
        session["site1_filter"] = filterA
        current_app.logger.debug(f"filterA da POST: {filterA}")
        # 1. Inizializziamo una lista per le condizioni e una per i parametri
        conditions = []
        params = []
        # Gestione filtro holidays
        if filterA == "wo_coord":
            conditions.append("(latitude IS NULL OR longitude IS NULL)")
        search_customer = request.form.get('searchCustomer')
        session["site1_search_customer"] = search_customer
        if search_customer:
            conditions.append("c.full_name LIKE %s")
            params.append(f"%{search_customer}%") # Il % lo mettiamo nel dato, non nella query
        # 2. Trasformiamo la lista di condizioni in una stringa WHERE
        searchStr = ""
        if conditions:
            searchStr = " WHERE " + " AND ".join(conditions)
        current_app.logger.debug(f"POST searchStr: {searchStr}")
        current_app.logger.debug(f"POST params: {params}") 
        session["site1_search"] = searchStr
        session["site1_search_params"] = [str(p) for p in params]

    db = get_db()
    cursor = db.cursor(dictionary=True)
    count_query = ('''SELECT COUNT(*) AS count FROM site s 
                   INNER JOIN customer c ON s.customer_id = c.id '''
                   + searchStr 
                )
    print(count_query)
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    offset = (page-1) * per_page 

    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')

    final_query = ('SELECT s.id, s.address AS address, s.city AS city, '
                   ' c.full_name AS customer_name, s.latitude, s.longitude '
            ' FROM site s INNER JOIN customer c ON s.customer_id = c.id ' +
             searchStr +
            ' ORDER BY c.full_name ASC LIMIT %s OFFSET %s'
        )
    print(final_query)
    # Aggiungiamo LIMIT e OFFSET alla lista dei parametri esistenti
    final_params = params + [per_page, offset]
    print(final_params)
    cursor.execute(final_query, final_params)
    sites = cursor.fetchall() 
    print(f"filterA: {filterA}")
    return render_template('site/index.html', sites=sites, pagination=pagination, search_customer=search_customer, filterA=filterA)

@bp.route('/site/create', methods=('GET', 'POST'))
@login_required
def create():
    customerList = get_customerList()
    if request.method == 'POST':
        customer_id = request.form['input_customer_id']
        city = request.form['city']
        address = request.form['address']
        contact_people = request.form['contact_people']
        telephone = request.form['telephone']
        email = request.form['email']
        error = None

        if (not customer_id) or (not city) or (not address):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO site (customer_id, city, address, contact_people, telephone, email)'
                ' VALUES (%s, %s, %s, %s, %s, %s)',
                (customer_id, city, address, contact_people, telephone, email)
            )
            db.commit()
            return redirect(url_for('site.index'))

    return render_template('site/create.html', customerList=customerList)

@bp.route('/site/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    current_app.logger.debug("id: " + str(id))
    site = get_site(id)
    customerList = get_customerList()
    customer_id = site['customer_id']
    
    if request.method == 'POST':
        current_app.logger.debug("Sono nella POST del update")
        customer_id = request.form['input_customer_id']
        city = request.form['city']
        address = request.form['address']
        contact_people = request.form['contact_people']
        telephone = request.form['telephone']
        email = request.form['email']
        #lat = request.form['lat']
        #lon = request.form['lon']
        lat = float(request.form['lat']) if request.form['lat'].strip() else None
        lon = float(request.form['lon']) if request.form['lon'].strip() else None
        error = None

        if (not customer_id) or (not city) or (not address):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE site SET customer_id = %s, city = %s, address = %s, contact_people = %s, ' \
                ' telephone = %s, email = %s, latitude=%s, longitude=%s'
                ' WHERE id = %s',
                (customer_id, city, address, contact_people, telephone, email, lat, lon, id)
            )
            db.commit()
            return redirect(url_for('site.index'))
    current_app.logger.debug("Sto per fare la return da update")
    return render_template('site/update.html', site=site, customerList=customerList)

@bp.route('/site/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM site WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('site.index'))

@bp.route('/site/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    site = get_site(id)
    customerList = get_customerList()
    return render_template('site/detail.html', site=site, customerList=customerList)

def get_site(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, customer_id, address, city, contact_people, telephone, email, latitude, longitude ' 
        ' FROM site'
        ' WHERE id = %s',
        (id,)
    )
    site = cursor.fetchone()

    if site is None:
        abort(404, f"site id {id} non esiste.")
    
    if site['contact_people'] == None:
        site['contact_people'] = ""
    if site['telephone'] == None:
        site['telephone'] = ""
    if site['email'] == None:
        site['email'] = ""

    return site

def get_customerList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, full_name, city'
        ' FROM customer ORDER BY full_name ASC'
    )
    customerList=cursor.fetchall()

    if customerList is None:
        abort(404, f"customerList è vuota.")
    return customerList
@bp.route('/site/geo_site', methods=('POST',))
@login_required
def geo_site():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id,CONCAT(s.address,",",s.city) AS full_address, c.full_name'
                ' FROM site s ' \
                ' INNER JOIN customer c ON s.customer_id = c.id' \
                ' WHERE latitude IS NULL OR longitude IS NULL'
                #' LIMIT 15'
                )
    sites = cursor.fetchall()
    # 1. Creiamo un buffer di memoria per il log
    buffer = io.StringIO()
    n=0
    for site in sites:
        if n == 50:
            break
        #print(site)
        site_id = site['id']
        latitudine, longitudine, messaggio_errore = geocoordinates(site['full_address'])
        #print(f"Lat: {latitudine} Long: {longitudine}")
        if not messaggio_errore:
            cursor.execute(
                'UPDATE site SET latitude=%s, longitude=%s'
                ' WHERE id=%s',
                (latitudine,longitudine,site_id)
                )
            db.commit()
        else:
            msg = messaggio_errore + ": " + site['full_name'] + " - " + site['full_address'] + "\n"
            print(msg)
            buffer.write(msg)
        n = n + 1
    output = buffer.getvalue()
    buffer.close()
    return Response(
        output,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=log.txt"}
    )
    #return redirect(url_for('site.index')) 