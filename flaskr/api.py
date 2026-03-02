from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flask import send_file, send_from_directory
#from flasgger import Swagger
from functools import wraps

bp = Blueprint('api', __name__)
API_KEY_VALIDA = "GaraAppalto2026_Secret_Token"
# --- DECORATORE DI SICUREZZA ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_key = request.headers.get('X-API-KEY')
        if user_key and user_key == API_KEY_VALIDA:
            return f(*args, **kwargs)
        return jsonify({
            "status": "unauthorized", 
            "message": "Accesso negato: API Key mancante o errata"
        }), 401
    return decorated_function

@bp.route('/api/v1/getActivities', methods=['GET']) # v1 nell'URL indica maturità del progetto
@require_api_key # <--- Il "buttafuori" della tua API
def get_activities():
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({"status": "error", "message": "Il parametro order_id è obbligatorio"}), 400
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT a.title AS Titolo, c.full_name AS Cliente, DATE_FORMAT(a.start,"%d/%m/%y") AS Data_inizio, DATE_FORMAT(a.end,"%d/%m/%y") AS Data_fine, s.address AS Indirizzo, s.city AS Città '
            ' FROM activity a ' 
            ' INNER JOIN p_order o ON o.id = a.p_order_id '
            ' INNER JOIN site s ON s.id = a.site_id '
            ' INNER JOIN customer c ON o.customer_id = c.id ' 
            ' WHERE o.closed=0 AND a.p_order_id = %s'
            ' ORDER BY c.full_name ASC, o.date DESC',(order_id,)
        )
        acts=cursor.fetchall()
        return jsonify({
            "status": "success",
            "count": len(acts),
            "data": acts
        }), 200
    except Exception as e:
        # Log dell'errore (importante per la manutenzione)
        print(f"Errore database: {e}")
        return jsonify({"status": "error", "message": "Errore interno del server"}), 500
    finally:
        cursor.close() # Sempre chiudere il cursore se non gestito da context manager

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Cerchiamo la chiave nell'header 'X-API-KEY'
        user_key = request.headers.get('X-API-KEY')
        if user_key and user_key == API_KEY_VALIDA:
            return f(*args, **kwargs)
        else:
            return jsonify({
                "status": "unauthorized",
                "message": "Accesso negato: API Key mancante o errata"
            }), 401
    return decorated_function