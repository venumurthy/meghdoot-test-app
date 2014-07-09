# -*- coding: utf-8 -*-
import httplib, json, os

AUTH_ENDPOINT_URL = '10.1.12.16:5000'
HEAT_ENDPOINT_URL = '10.1.12.16:8004'

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

class Stacks(object):
  def __init__(self, tenant_id, token):
    self.tenant_id = tenant_id
    self.token = token

  def _headers(self):
    return {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "X-Auth-Token": self.token
    }

  def _create_stack(self, params):
    print "Attempting to create heat stack %s...\n" % params['stack_name']
    conn = httplib.HTTPConnection(HEAT_ENDPOINT_URL)
    conn.request("POST", "/v1/{tenant_id}/stacks".format(tenant_id=self.tenant_id), json.dumps(params), self._headers())
    response = conn.getresponse().read()
    conn.close()
    return response

  def _update_stack(self, stack_id, params):
    stack_name = params['stack_name']
    print "Attempting to update heat stack %s...\n" % stack_name
    conn = httplib.HTTPConnection(HEAT_ENDPOINT_URL)
    endpoint = "/v1/{tenant_id}/stacks/{stack_name}/{stack_id}".format(tenant_id=self.tenant_id,
                                                                       stack_name=stack_name,
                                                                       stack_id=stack_id)
    conn.request("PUT", endpoint, json.dumps(params), self._headers())
    response = conn.getresponse().read()
    conn.close()
    return response

  def get_stack(self, stack_name):
    print 'Fetching stack with name: %s' % stack_name
    conn = httplib.HTTPConnection(HEAT_ENDPOINT_URL)
    endpoint = "/v1/{tenant_id}/stacks/{stack_name}".format(tenant_id=self.tenant_id,
                                                            stack_name=stack_name)
    conn.request("GET", endpoint, json.dumps({}), self._headers())
    exists_response = conn.getresponse()
    conn.close()
    return exists_response

  def create_or_update(self, params):
    exists_response = self.get_stack(params['stack_name'])

    if exists_response.status == 404:
      self._create_stack(params)

    elif exists_response.status == 302:
      stack_id = exists_response.getheader('Location').split('/')[-1]
      self._update_stack(stack_id, params)

if __name__ == "__main__":
  USERNAME = os.environ['OS_USERNAME']
  PASSWORD = os.environ['OS_PASSWORD']
  TENANT_NAME = os.environ['OS_TENANTNAME']
  STACK_NAME = os.environ['HEAT_STACK_NAME']
  TENANT_ID = 'a9d08118cbf14b6fbf353f04a3a58704'

  user = UserAuth(TENANT_NAME, USERNAME, PASSWORD)

  try:
    token = user.get_token()
  except AuthError:
    print 'Received error when trying to authenticate user: {username}'.format(username = USERNAME)
    raise

  params = {
    "stack_name": STACK_NAME,
    "template_url": "https://raw.githubusercontent.com/asifrc/meghdoot-test-app/master/hot/meghdoottestapp.yml"
  }

  Stacks(TENANT_ID, token).create_or_update(params)
  print "Deployment complete"