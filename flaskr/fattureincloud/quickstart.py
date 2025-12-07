import fattureincloud_python_sdk
from fattureincloud_python_sdk.api import user_api
#from fattureincloud_python_sdk.api import suppliers_api
from fattureincloud_python_sdk.api import clients_api
from fattureincloud_python_sdk.models.list_user_companies_response import ListUserCompaniesResponse
from fattureincloud_python_sdk.api import issued_documents_api
import json
import collections
collections.Callable = collections.abc.Callable #needed if you are using python > 3.10


class Quickstart:
    def get_company_orders(self):
        print("Quickstart nuova 2")
        token_file = open("./token.json")
        json_file = json.load(token_file)
        token_file.close()
        configuration = fattureincloud_python_sdk.Configuration()
        configuration.access_token = json_file["access_token"]
        
    
        with fattureincloud_python_sdk.ApiClient(configuration) as api_client:
            # Retrieve the first company id
            user_api_instance = user_api.UserApi(api_client)
            user_companies_response = user_api_instance.list_user_companies()
            first_company_id = user_companies_response.data.companies[0].id
            print("Numero di company definite: " + str(len(user_companies_response.data.companies)))
            print("First Company ID:" + str(first_company_id))

            # Retrieve the list of the Orders
            api_instance = issued_documents_api.IssuedDocumentsApi(api_client)
            #clients_api_instance = clients_api.ClientsApi(api_client)
            orders = api_instance.list_issued_documents(company_id=first_company_id,type="order")
            #company_clients = clients_api_instance.list_clients(first_company_id)

            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes(str(orders.data), "utf8"))
            #self.wfile.write(bytes(str(company_clients.data), "utf8"))
        return