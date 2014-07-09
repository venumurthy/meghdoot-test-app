# -*- coding: utf-8 -*-
import httplib, urllib, json, os

username = os.environ['OS_USERNAME']
password = os.environ['OS_PASSWORD']
tenant_name = os.environ['OS_TENANTNAME']
stack_name = os.environ['HEAT_STACK_NAME']

# Get Authentication Token from Keystone

print "Authenticating to KeyStone...\n"

headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "User-Agent": "python-eoddeploy"
}
params = {
  "auth": {
    "tenantName": tenant_name,
    "passwordCredentials":{
      "username": username,
      "password": password
    }
  }
}
conn = httplib.HTTPConnection("10.1.12.16:5000")
conn.request("POST", "/v2.0/tokens", json.dumps(params), headers)
response = conn.getresponse().read()
conn.close()

auth_token = json.loads(response)['access']['token']['id']

print "Authenticated.\n"

# Authenticated Header
headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Auth-Token": auth_token
}


# Check if Stack Exists
print 'Checking if stack exists'

params = {
  "stack_name": stack_name,
  "template_url": "https://raw.githubusercontent.com/asifrc/meghdoot-test-app/master/hot/meghdoottestapp.yml"
}
conn = httplib.HTTPConnection("10.1.12.16:8004")
conn.request("GET", "/v1/a9d08118cbf14b6fbf353f04a3a58704/stacks/%s" % stack_name, json.dumps({}), headers)
exists_response = conn.getresponse()
exists_body = exists_response.read()

conn.close()
print "The stack query returned: %s" % exists_response.status

if exists_response.status == 404:
  # creating a stack
  print "Attempting to deploy heat template...\n"
  params = {
    "stack_name": stack_name,
    "template_url": "https://raw.githubusercontent.com/asifrc/meghdoot-test-app/master/hot/meghdoottestapp.yml"
  }
  conn = httplib.HTTPConnection("10.1.12.16:8004")
  conn.request("POST", "/v1/a9d08118cbf14b6fbf353f04a3a58704/stacks", json.dumps(params), headers)
  response = conn.getresponse().read()
  conn.close()
  print response
elif exists_response.status == 302:
  print "Attempting to update heat stack...\n"
  stack_id = exists_response.getheader('Location').split('/')[-1]
  print stack_id
  params = {
    "stack_name": stack_name,
    "template_url": "https://raw.githubusercontent.com/asifrc/meghdoot-test-app/master/hot/meghdoottestapp.yml"
  }
  conn = httplib.HTTPConnection("10.1.12.16:8004")
  conn.request("PUT", "/v1/a9d08118cbf14b6fbf353f04a3a58704/stacks/%s/%s" % (stack_name, stack_id), json.dumps(params), headers)
  response = conn.getresponse().read()
  conn.close()
  print response






print "Complete."
