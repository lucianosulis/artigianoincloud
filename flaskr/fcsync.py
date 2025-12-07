from flask import Flask, redirect, url_for, request, flash, current_app, g, session
from flaskr.db import get_db
import json, pprint
from pprint import pprint
import fattureincloud_python_sdk
from fattureincloud_python_sdk.api import user_api
#from fattureincloud_python_sdk.api import suppliers_api
from fattureincloud_python_sdk.api import clients_api
from fattureincloud_python_sdk.models.list_user_companies_response import ListUserCompaniesResponse
from fattureincloud_python_sdk.oauth2.oauth2 import OAuth2AuthorizationCodeManager
from fattureincloud_python_sdk.oauth2.oauth2 import Scope
from fattureincloud_python_sdk.api import issued_documents_api
from fattureincloud_python_sdk.models.list_issued_documents_response import ListIssuedDocumentsResponse
from fattureincloud_python_sdk.models.issued_document import IssuedDocument
from fattureincloud_python_sdk.models.create_issued_document_request import CreateIssuedDocumentRequest
from fattureincloud_python_sdk.models.issued_document_type import IssuedDocumentType
from fattureincloud_python_sdk.models.entity import Entity
from fattureincloud_python_sdk.models.client import Client
from fattureincloud_python_sdk.models.client_type import ClientType
from fattureincloud_python_sdk.models.create_client_request import CreateClientRequest
from fattureincloud_python_sdk.models.create_client_response import CreateClientResponse
from fattureincloud_python_sdk.models.issued_document_items_list_item import IssuedDocumentItemsListItem
from fattureincloud_python_sdk.models.issued_document_payments_list_item import IssuedDocumentPaymentsListItem

from datetime import datetime
from dateutil.relativedelta import relativedelta

class Oauth:
    def get_oauth_access_token(self):
        session["activity_first_page"] = 'Y'
        #print(session["fc_call_type"])
        current_app.config.from_file("config.json", load=json.load)
        #oauth = OAuth2AuthorizationCodeManager('Aw8Tn3tOvSPXXYHBUOWGD5AXur4iF79p', '27v9eQIt6PRpJZXMOOmH6xRTT9jJUCrbkCWUrV7BpDi03iwelNft4vlrxHG5javw', 'http://localhost:5000/oauth')
        oauth = OAuth2AuthorizationCodeManager(current_app.config["FC_CLIENT_ID"], current_app.config["FC_CLIENT_SECRET"], current_app.config["FC_REDIRECT_URI"])
        url = oauth.get_authorization_url([Scope.ISSUED_DOCUMENTS_ORDERS_ALL,Scope.ENTITY_CLIENTS_ALL,Scope.ENTITY_SUPPLIERS_READ], 'AveUjKtZ')
        #print("url da Oauth: " + url)
        params = request.args
        #print(request.args.to_dict().items())
        if 'code' in params:  #In questo caso è una call-back da Fattureincloud, altrimenti è la chiamata iniziale vuota
            code = params['code']
            #print("code: " + code)
            token = oauth.fetch_token(code)
            #print(token)
            file = open('token.json', 'w')
            file.write(json.dumps({"access_token": token.access_token}))  #saving the oAuth access token in the token.json file
            file.close()
            db = get_db()
            cursor = db.cursor()
            token_file = open("token.json")
            json_file = json.load(token_file)
            token_file.close()
            configuration = fattureincloud_python_sdk.Configuration()
            configuration.access_token = json_file["access_token"]

            with fattureincloud_python_sdk.ApiClient(configuration) as api_client:
                # Retrieve the first company id
                user_api_instance = user_api.UserApi(api_client)
                user_companies_response = user_api_instance.list_user_companies()
                first_company_id = user_companies_response.data.companies[0].id
                #print("first_company_id: " + str(first_company_id))
                customers_api_instance = clients_api.ClientsApi(api_client)
                documents_api_instance = issued_documents_api.IssuedDocumentsApi(api_client)

                if session["fc_call_type"] == "fc_sync":
                    #Sincronizzo i clienti
                    customers = customers_api_instance.list_clients(first_company_id,page=1)
                    last_page = customers.last_page
                    i = 0
                    cust_total_insert=0
                    cust_total_update=0
                    order_total_insert=0
                    order_total_update=0
                    order_wo_customer = 0
                    while i < last_page:
                        i = i + 1
                        #print(i)
                        customers = customers_api_instance.list_clients(first_company_id, page = i, fieldset = 'detailed')
                        for customer in customers.data:
                            #print(customer.address_street)
                            if customer.id != None:
                                #print("Diverso da None") 
                                cursor.execute(
                                    'SELECT id FROM customer where id=%s',
                                    (customer.id,)
                                )
                                record = cursor.fetchone() 
                                
                                if record == None:
                                    print("Inserisco nuovo customer")
                                    print(customer.name)
                                    cust_total_insert = cust_total_insert + 1
                                    cursor.execute(
                                        'INSERT INTO customer (id, full_name, address, city, zip_code)'
                                        ' VALUES (%s, %s, %s, %s, %s)',
                                        (customer.id, customer.name, customer.address_street, customer.address_city, customer.address_postal_code)
                                    )
                                    db.commit()
                                    cursor.execute(
                                        'INSERT INTO site (customer_id, address, city)'
                                        ' VALUES (%s, %s, %s)',
                                        (customer.id, customer.address_street, customer.address_city)
                                    )
                                    db.commit()

                                else:
                                    cust_total_update = cust_total_update + 1
                                    cursor.execute(
                                        'UPDATE customer SET full_name=%s, address=%s, city=%s, zip_code=%s'
                                        ' WHERE id=%s',
                                        (customer.name, customer.address_street, customer.address_city, customer.address_postal_code, customer.id)
                                    )
                                    db.commit()
                    #Sincronizzo gli ordini
                    orders = documents_api_instance.list_issued_documents(company_id=first_company_id,type="order",page=1, fieldset = 'detailed')
                    last_page = orders.last_page
                    print("last_page=" + str(last_page))
                    i=0
                    while i < last_page:
                        i = i + 1
                        orders = documents_api_instance.list_issued_documents(company_id=first_company_id,type="order",page=i, fieldset = 'detailed')
                        for order in orders.data:
                            #if i==1:
                            #    print(order)
                            if order.numeration == "/S":
                                order_type = 'spot'
                                #print("ordine spot - " + str(order.var_date) + " - " + str(order.entity.id) + " - " + order.visible_subject)
                            else:
                                order_type = 'cont'
                                #print("ordine cont - " + str(order.var_date) + " - " + str(order.entity.id) + " - " + order.visible_subject)
                            if order.entity.id != None:
                                #print("Ordine con cliente")
                                cursor.execute(
                                    'SELECT id FROM p_order where id=%s',
                                    (order.id,))
                                record = cursor.fetchone() 
                                
                                if record == None:
                                    print("Inserisco nuovo ordine: " + order.visible_subject)
                                    order_total_insert = order_total_insert + 1
                                    cursor.execute(
                                        'INSERT INTO p_order (id, customer_id, description, amount, date, order_type, notes)'
                                        ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                                        (order.id, order.entity.id, order.visible_subject, order.amount_net, str(order.var_date), order_type, order.notes)
                                    )
                                    db.commit()
                                else:
                                    order_total_update = order_total_update + 1
                                    print ("Note prese fa Fattureincloud:")
                                    print(order.notes)
                                    cursor.execute(
                                        'UPDATE p_order SET customer_id=%s, description=%s, amount=%s, date=%s, order_type=%s, notes=%s'
                                        ' WHERE id=%s',
                                        (order.entity.id, order.visible_subject, order.amount_net, str(order.var_date), order_type, order.notes, order.id)
                                    )
                                    db.commit()
                            else:
                                order_wo_customer = order_wo_customer + 1
                    flash("Dati scaricati da Fatture in Cloud - Clienti inseriti: " + str(cust_total_insert) + ", Clienti aggiornati: " + str(cust_total_update) + ", Ordini inseriti: " + str(order_total_insert) + ", Ordini aggiornati: " + str(order_total_update) + ", Ordini non scaricati perché senza anagrafica cliente: " + str(order_wo_customer))                    
                                
                elif session["fc_call_type"] == "fc_new_order": 
                    print("Creo nuovo ordine spot con seguente attività")
                    customer_id = session["customer_id"]
                    title = session["title"]
                    order_notes = session["notes"]
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'SELECT c.id, c.full_name, c.address, c.city'
                        ' FROM customer c'
                        ' WHERE c.id = %s', (customer_id,)
                    )
                    row = cursor.fetchone()
                    customerFullName = row['full_name']
                    print("customerFullName: " + customerFullName)
                    #Creo ordine in FC
                    entity = Entity(
                            id=int(customer_id),
                            name=customerFullName,
                            #vat_number="47803200154",
                            #tax_code="RSSMRA91M20B967Q",
                            #address_street="Via Italia, 66",
                            #address_postal_code="20900",
                            #address_city="Milano",
                            #address_province="MI",
                            #country="Italia"
                        )
                    order = IssuedDocument(type = IssuedDocumentType("order"),
                        entity = entity,
                        date = datetime.today().strftime('%Y-%m-%d'),
                        subject = title,
                        visible_subject = title,
                        numeration = '/S',
                        notes = order_notes
                    )
                    create_issued_document_request = CreateIssuedDocumentRequest(data = order)
                    try:
                            print("Sto per creare il nuovo ordine")
                            api_response = documents_api_instance.create_issued_document(first_company_id, create_issued_document_request=create_issued_document_request)
                            order_id = api_response.data.id
                            print("order_id: " + str(order_id))
                    except fattureincloud_python_sdk.ApiException as e:
                            print("Exception when calling IssuedDocumentsApi->create_issued_document: %s\n" % e)
                    flash("Ordine per questa attività creato in Fatture in Cloud.")
                    #Adesso creo il record della attività in Artigiano in Cloud
                    site_id = session["site_id"]
                    description = session["description"]
                    start = session["start"]
                    end = session["end"]
                    date = datetime.today().strftime('%Y-%m-%d')
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    #Creo il nuovo record per l'ordine
                    cursor.execute(
                        'INSERT INTO p_order (id, description, customer_id, date, order_type, notes)'
                        ' VALUES (%s, %s, %s, %s, %s, %s)',
                        (order_id, title, customer_id, date, 'spot', order_notes)
                    )
                    db.commit()
                    #Creo il nuovo record per l'attività
                    cursor.execute(
                        'INSERT INTO activity (title, description, start, end, p_order_id, site_id)'
                        ' VALUES (%s, %s, %s, %s, %s, %s)',
                        (title, description, start, end, order_id, site_id)
                    )
                    db.commit()
                    
                    cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
                    row = cursor.fetchone()
                    id = row['last_insert']
                    #aggiungere le eventuali relazioni con team

                elif session["fc_call_type"] == "fc_new_order_wo_act": 
                    print("Creo nuovo ordine spot senza attività")
                    customer_id = session["customer_id"]
                    title = session["title"]
                    order_notes = session["notes"]
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'SELECT c.id, c.full_name, c.address, c.city'
                        ' FROM customer c'
                        ' WHERE c.id = %s', (customer_id,)
                    )
                    row = cursor.fetchone()
                    customerFullName = row['full_name']
                    print("customerFullName: " + customerFullName)
                    #Creo ordine in FC
                    entity = Entity(
                            id=int(customer_id),
                            name=customerFullName,
                        )
                    order = IssuedDocument(type = IssuedDocumentType("order"),
                        entity = entity,
                        date = datetime.today().strftime('%Y-%m-%d'),
                        subject = title,
                        visible_subject = title,
                        numeration = '/S',
                        notes = order_notes
                    )
                    create_issued_document_request = CreateIssuedDocumentRequest(data = order)
                    try:
                            print("Sto per creare il nuovo ordine")
                            api_response = documents_api_instance.create_issued_document(first_company_id, create_issued_document_request=create_issued_document_request)
                            order_id = api_response.data.id
                            print("order_id: " + str(order_id))
                    except fattureincloud_python_sdk.ApiException as e:
                            print("Exception when calling IssuedDocumentsApi->create_issued_document: %s\n" % e)
                    flash("Ordine creato in Fatture in Cloud.")
                    #Adesso creo il record dell'ordine in Artigiano in Cloud
                    description = session["title"]
                    date = datetime.today().strftime('%Y-%m-%d')
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO p_order (id, description, customer_id, date, order_type)'
                        ' VALUES (%s, %s, %s, %s, %s)',
                        (order_id, title, customer_id, date, 'spot')
                    )
                    db.commit()
                
                elif session["fc_call_type"] == "fc_new_order_new_cust": 
                    print("Creo nuovo ordine spot senza attività ma prima creo nuovo cliente")
                    entity = Client(
                    type = ClientType("company"),
                    name = session["customer_name"],
                    address_street = session["customer_address"],
                    address_city = session["customer_city"],
                    )
                    # Here we put our entity in the request object
                    create_client_request = CreateClientRequest(
                        data = entity
                    )
                    # Now we are all set for the final call
                    # Create the client: https://github.com/fattureincloud/fattureincloud-python-sdk/blob/master/docs/ClientsApi.md#create_client
                    with fattureincloud_python_sdk.ApiClient(configuration) as api_client:
                        api_instance = clients_api.ClientsApi(api_client)
                        try:
                            api_response = api_instance.create_client(first_company_id, create_client_request=create_client_request)
                            pprint(api_response)
                            customer_id = api_response.data.id
                            print("customer_id: " + str(customer_id))
                        except fattureincloud_python_sdk.ApiException as e:
                            print("Exception when calling ClientsApi->create_client: %s\n" % e)
                            if e.reason == "Conflict":
                                flash("Errore: il cliente esiste già. Selezionalo dalla anagrafica.")
                            else:
                                flash("Errore nella creazione del cliente: %s\n" % e.reason)
                            return (url_for("order.index"))
                    #Creo il cliente anche in Artigianoincloud
                    db = get_db()
                    cursor.execute(
                        'INSERT INTO customer (id, full_name, address, city)'
                        ' VALUES (%s, %s, %s, %s)',
                        (customer_id, session["customer_name"], session["customer_address"], session["customer_city"])
                        )
                    db.commit()
                    #Creo il site per il cliente appena creato (sede principale)
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO site (customer_id, city, address)'
                        ' VALUES (%s, %s, %s)',
                        (customer_id, session["customer_city"], session["customer_address"])
                    )
                    db.commit()
                    title = session["title"]
                    order_notes = session["notes"]
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'SELECT c.id, c.full_name, c.address, c.city'
                        ' FROM customer c'
                        ' WHERE c.id = %s', (customer_id,)
                    )
                    row = cursor.fetchone()
                    customerFullName = row['full_name']
                    print("customerFullName: " + customerFullName)
                    #Creo ordine in FC
                    entity = Entity(
                            id=int(customer_id),
                            name=customerFullName,
                        )
                    order = IssuedDocument(type = IssuedDocumentType("order"),
                        entity = entity,
                        date = datetime.today().strftime('%Y-%m-%d'),
                        subject = title,
                        visible_subject = title,
                        numeration = '/S', 
                        notes = order_notes
                    )
                    create_issued_document_request = CreateIssuedDocumentRequest(data = order)
                    try:
                            print("Sto per creare il nuovo ordine")
                            api_response = documents_api_instance.create_issued_document(first_company_id, create_issued_document_request=create_issued_document_request)
                            order_id = api_response.data.id
                            print("order_id: " + str(order_id))
                    except fattureincloud_python_sdk.ApiException as e:
                            print("Exception when calling IssuedDocumentsApi->create_issued_document: %s\n" % e)
                    flash("Ordine creato in Fatture in Cloud.")
                    #Adesso creo il record dell'ordine in Artigiano in Cloud
                    description = session["title"]
                    date = datetime.today().strftime('%Y-%m-%d')
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO p_order (id, description, customer_id, date, order_type, notes)'
                        ' VALUES (%s, %s, %s, %s, %s, %s)',
                        (order_id, title, customer_id, date, 'spot', order_notes)
                    )
                    db.commit()

                elif session["fc_call_type"] == "fc_new_order_duplicate": 
                    print("Creo nuovo ordine duplicato")
                    customer_id = session["customer_id"]
                    title = session["title"]
                    order_date = session["order_date"]
                    order_amount = float(session["order_amount"])
                    order_notes = session["notes"]
                    print("order_amount:")
                    print(order_amount)
                    if session["order_type"] == "spot":
                         order_numeration = '/S'
                    else:
                         order_numeration = ''
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'SELECT c.id, c.full_name, c.address, c.city'
                        ' FROM customer c'
                        ' WHERE c.id = %s', (customer_id,)
                    )
                    row = cursor.fetchone()
                    customerFullName = row['full_name']
                    print("customerFullName: " + customerFullName)
                    #Creo ordine in FC
                    entity = Entity(
                            id=int(customer_id),
                            name=customerFullName,
                        )
                    item = IssuedDocumentItemsListItem(
                            name='Totale ordine',
                            qty=1,
                            net_price=order_amount
                        )
                    itemList = [item]
                    payment = IssuedDocumentPaymentsListItem(
                            amount=order_amount*1.22,
                            due_date = order_date
                        )
                    paymentList = [payment]

                    order = IssuedDocument(type = IssuedDocumentType("order"),
                        entity = entity,
                        date = order_date,
                        subject = title,
                        visible_subject = title,
                        numeration = order_numeration,
                        items_list = itemList,
                        payments_list = paymentList,
                        notes = order_notes
                        
                    )
                    create_issued_document_request = CreateIssuedDocumentRequest(data = order)
                    try:
                            print("Sto per creare il nuovo ordine")
                            api_response = documents_api_instance.create_issued_document(first_company_id, create_issued_document_request=create_issued_document_request)
                            order_id = api_response.data.id
                            print("order_id: " + str(order_id))
                    except fattureincloud_python_sdk.ApiException as e:
                            print("Exception when calling IssuedDocumentsApi->create_issued_document: %s\n" % e)
                    flash("Ordine creato in Fatture in Cloud.")
                    #Adesso creo il record dell'ordine in Artigiano in Cloud
                    description = session["title"]
                    #date = datetime.today().strftime('%Y-%m-%d')
                    date = session["order_date"]
                    amount = session["order_amount"]
                    notes = session["notes"]
                    order_type = session["order_type"]
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                        'INSERT INTO p_order (id, description, customer_id, date, order_type, amount, notes)'
                        ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (order_id, title, customer_id, date, order_type, amount, notes)
                    )
                    db.commit()
                    print("Sto per duplicare po_invoices")
                    #Duplico anche le eventuali scadenze di fatturazione spostandole di un anno
                    cursor = db.cursor(dictionary=True)
                    cursor.execute(
                         ' SELECT * FROM po_invoices WHERE order_id = %s',
                            (session["old_order_id"],)
                    )
                    po_invoices = cursor.fetchall()
                    if po_invoices is not None:
                        for po_invoice in po_invoices:
                          new_date = po_invoice['date'] + relativedelta(years=1)
                          cursor = db.cursor(dictionary=True)
                          cursor.execute(
                            'INSERT INTO po_invoices (order_id, date, amount, invoiced, proforma)'
                            ' VALUES (%s, %s, %s, %s, %s)',
                            (order_id, new_date, po_invoice['amount'], po_invoice['invoiced'], po_invoice['proforma'])
                            )
                        db.commit()  
                    
                else:
                   flash("Errore non previsto.") 

            if session["fc_call_type"] == "fc_new_order_wo_act" or session["fc_call_type"] == "fc_new_order_new_cust" or session["fc_call_type"] == "fc_new_order_duplicate":
                return (url_for("order.index"))
            else:
                return (url_for("activity.index")) 
        return url
    

        
