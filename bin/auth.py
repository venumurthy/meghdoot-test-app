import httplib, json, os

AUTH_ENDPOINT_URL = os.environ['KEYSTONE_URL']

class AuthError(Exception):
  pass

class UserAuth(object):
  def __init__(self, tenant_name, username, password):
    self.tenant_name = tenant_name
    self.username = username
    self.password = password

  def get_token(self):
    print "Authenticating to Keystone...\n"

    headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "User-Agent": "python-eoddeploy"
    }
    params = {
      "auth": {
        "tenantName": self.tenant_name,
        "passwordCredentials":{
          "username": self.username,
          "password": self.password
        }
      }
    }
    conn = httplib.HTTPConnection(AUTH_ENDPOINT_URL)
    conn.request("POST", "/v2.0/tokens", json.dumps(params), headers)
    auth_response = json.loads(conn.getresponse().read())
    conn.close()

    if 'error' in auth_response:
      raise AuthError('Authentication was unsuccessful')

    print "Authenticated successfully\n"
    return auth_response['access']['token']['id']
