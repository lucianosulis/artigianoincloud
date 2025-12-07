import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
from fattureincloud_python_sdk.oauth2.oauth2 import OAuth2AuthorizationCodeManager
from fattureincloud_python_sdk.oauth2.oauth2 import Scope

class Oauth:
    def get_oauth_access_token(self):
        print("Sono qui")
        #oauth = OAuth2AuthorizationCodeManager('CLIENT_ID', 'CLIENT_SECRET', 'http://localhost:8000/oauth')
        oauth = OAuth2AuthorizationCodeManager('Aw8Tn3tOvSPXXYHBUOWGD5AXur4iF79p', '27v9eQIt6PRpJZXMOOmH6xRTT9jJUCrbkCWUrV7BpDi03iwelNft4vlrxHG5javw', 'http://localhost:5000/fcauth')
        query_components = parse_qs(urlparse(self.path).query)
        if 'code' in query_components:
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            code = query_components['code'][0]
            token = oauth.fetch_token(code)
            file = open('./token.json', 'w')
            file.write(json.dumps({"access_token": token.access_token}))  #saving the oAuth access token in the token.json file
            file.close()
            self.wfile.write(bytes('Token saved succesfully in ./token.json', 'utf8'))
        else:
            #url = oauth.get_authorization_url([Scope.ENTITY_SUPPLIERS_READ], 'EXAMPLE_STATE')
            #url = oauth.get_authorization_url([Scope.ENTITY_CLIENTS_READ,Scope.ENTITY_SUPPLIERS_READ], 'EXAMPLE_STATE') 
            url = oauth.get_authorization_url([Scope.ISSUED_DOCUMENTS_ORDERS_READ,Scope.ENTITY_CLIENTS_READ,Scope.ENTITY_SUPPLIERS_READ], 'EXAMPLE_STATE')
            #url = oauth.get_authorization_url([Scope.ISSUED_DOCUMENTS_ORDERS_READ], 'EXAMPLE_STATE') 
            self.send_response(302)
            self.send_header('Location', url)
            self.end_headers()
        return