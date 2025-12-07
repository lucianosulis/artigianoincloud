from http.server import BaseHTTPRequestHandler, HTTPServer
from oauth import Oauth #import the Oauth class
from quickstart import Quickstart #import the Quickstart class
#quickstart.reload(quickstart)
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #url routing
        if self.path.startswith('/oauth'): #oauth endpoint
            Oauth.get_oauth_access_token(self)
        elif self.path == '/quickstart': #quickstart endpoint
            print("endpoint: /quickstart")
            Quickstart.get_company_orders(self)
        return
    
def run():
    print('Avvio del server sulla porta 8000...')
    server_address = ('127.0.0.1', 8000) #set your hostname and port
    httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
    print('Server in esecuzione...')
    httpd.serve_forever()
run()