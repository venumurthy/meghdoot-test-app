# -*- coding: utf-8 -*-
import httplib, urllib, json, os

username = os.environ['OS_USERNAME']
password = os.environ['OS_PASSWORD']
tenant_name = os.environ['OS_TENANTNAME']

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

print "Attempting to deploy heat template...\n"

# Spin up template using Heat API
headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Auth-Token": auth_token
}
params = {
  "stack_name": "DeployTest",
  "template_url": "https://raw.githubusercontent.com/asifrc/meghdoot-test-app/master/hot/meghdoottestapp.yml"
}
conn = httplib.HTTPConnection("10.1.12.16:8004")
conn.request("POST", "/v1/a9d08118cbf14b6fbf353f04a3a58704/stacks", json.dumps(params), headers)
response = conn.getresponse().read()
conn.close()

print response

print "Complete."
