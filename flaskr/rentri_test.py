from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flask import send_file, send_from_directory
import requests
import base64
import hashlib
import jwt
import time
import uuid
from cryptography.hazmat.primitives import serialization
from cryptography import x509
import os
import fitz  # PyMuPDF

bp = Blueprint('rentri', __name__)

@bp.route('/rentri', methods=('GET', 'POST'))
@login_required
def index():
    session["activity_first_page"] = 'Y'
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    if request.method == 'POST': 
        
        path = current_app.config["WS_PATH"] 
        nome_file = "FIR di prova.pdf"
        output_path = path + nome_file
        # Percorso PDF di partenza
        #pdf_path = output_path  # usa il nome corretto ottenuto prima
        #new_path = path + "file_fir_modificato.pdf"
        # Apri il PDF

        doc = fitz.open(output_path)
        # Scegli su quale pagina scrivere (es. la prima)
        page = doc[0]  # attenzione: è zero-based (0 = prima pagina)
        # Scrivi del testo alla posizione (x=50, y=100)
        page.insert_text(
            (112, 83),  # coordinate in punti
            "PRONTOGIARDINI S.R.L.",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (112, 108),  # coordinate in punti
            "Via San Cassiano 1 - 24030 Mapello (BG)",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (112, 119),  # coordinate in punti
            "Fonderie Mazzucconi SPA - Via Mazzini 10 - Ponte San Pietro",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (112, 137),  # coordinate in punti
            "04721650168",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (365, 137),  # coordinate in punti
            "MI85294",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (112, 368),  # coordinate in punti
            "20.02.01",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (112, 382),  # coordinate in punti
            "Rifiuti biodegradabili",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (218, 399),  # coordinate in punti
            "X",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        page.insert_text(
            (543, 399),  # coordinate in punti
            "X",  # testo da scrivere
            fontsize=8,
            fontname="helv",  # Helvetica
            color=(0, 0, 0),  # nero (RGB da 0 a 1)
        )
        # Salva il file modificato
        doc.save(output_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

        #flash(f"FIR {numero_fir} generato con successo.")
        return send_from_directory(path, nome_file, as_attachment=True)
    return render_template('rentri/index.html')

def authorize(method):
    current_app.config.from_file("config.json", load=json.load)
    path_cert = current_app.config["PATH_CERT"]
    # === CONFIGURAZIONE ===
    CERT_FILE = path_cert + "cert.pem"  # certificato in PEM
    KEY_FILE = path_cert + "key.pem"    # chiave privata in PEM
    cert = (CERT_FILE,KEY_FILE)
    #print("Cert file exists?", os.path.exists(CERT_FILE))
    #print("Key file exists?", os.path.exists(KEY_FILE))
    BODY = ""  # corpo della richiesta, qui è GET quindi vuoto
    API_AUDIENCE = "rentrigov.demo.api"
    # === 1. CARICA CERTIFICATO E CHIAVE PRIVATA ===
    with open(CERT_FILE, "rb") as cert_file:
        cert_data = cert_file.read()
        cert_obj = x509.load_pem_x509_certificate(cert_data)
        cert_b64 = base64.b64encode(cert_obj.public_bytes(serialization.Encoding.DER)).decode("utf-8")
    with open(KEY_FILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    # === 2. GENERA IL JWT PER Authorization ===
    now = int(time.time())
    payload = {
        "iss": "04721650168",  # CF o P.IVA del soggetto accreditato
        "aud": API_AUDIENCE,
        "exp": now + 300,
        "jti": str(uuid.uuid4())
    }
    auth_headers = {
        "alg": "ES256",
        "typ": "JWT",
        "x5c": [cert_b64]
    }
    jwt_token = jwt.encode(payload, private_key, algorithm="ES256", headers=auth_headers)
    # === 3. GENERA DIGEST SHA-256 (body vuoto nel tuo caso) ===
    digest_value = base64.b64encode(hashlib.sha256(BODY.encode("utf-8")).digest()).decode("utf-8")
    digest_header = f"SHA-256={digest_value}"
    # === 4. COSTRUISCI Agid-JWT-Signature ===
    signature_payload = {
        "iat": now,
        "nbf": now,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
        "identificativo": "04721650168",
        "signed_headers": [
            {"Digest": digest_header}
        ]
    }
    agid_jwt_signature = jwt.encode(signature_payload, private_key, algorithm="ES256", headers=auth_headers)
    
    if method == 'POST':
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Digest": digest_header,
            "Agid-JWT-Signature": agid_jwt_signature,
            "Content-Type": "application/json"
        }
    else:
        headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Digest": digest_header,
                "Agid-JWT-Signature": agid_jwt_signature,
                "Accept": "application/json, application/problem+json"
        }
    return(headers, cert)
