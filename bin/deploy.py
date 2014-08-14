# -*- coding: utf-8 -*-
"""Heat Template Generator

Usage:
  templatey.py [-i=<instance_count>] -a=<app_setup_script_path> -b=<db_setup_script_path>
  templatey.py (-h | --help)
  templatey.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  -i=<instance_count>          Number of instances [default: 1].
  -a=<app_setup_script_path>       Path to the application setup script.
  -b=<db_setup_script_path>       Path to the database setup script.

"""
from contextlib import closing
import httplib
import json
import os
import sys
import time

from docopt import docopt

from auth import UserAuth, AuthError
from templatey import Generator


class StackActionError(Exception):
    pass


class Stacks(object):

    def __init__(self, tenant_id, token, endpoint):
        self.tenant_id = tenant_id
        self.token = token
        self.HEAT_ENDPOINT_URL = endpoint

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": self.token
        }

    def _create_stack(self, params):
        print "Attempting to create heat stack %s...\n" % params['stack_name']
        with closing(httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)) as conn:
            conn.request("POST", "/v1/{tenant_id}/stacks".format(tenant_id=self.tenant_id), json.dumps(params), self._headers())
            response = conn.getresponse()
            response_contents = response.read()
            status = response.status
        if status != httplib.CREATED:
            raise StackActionError(self._format_response(status, response_contents)['error'])


    def _update_stack(self, stack_id, params):
        stack_name = params['stack_name']
        print "Attempting to update heat stack %s...\n" % stack_name

        endpoint = "/v1/{tenant_id}/stacks/{stack_name}/{stack_id}".format(tenant_id=self.tenant_id,
                                                                           stack_name=stack_name,
                                                                           stack_id=stack_id)

        with closing(httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)) as conn:
            conn.request("PUT", endpoint, json.dumps(params), self._headers())
            response = conn.getresponse()
            response_contents = response.read()
            status = response.status
        if status != httplib.ACCEPTED:
            raise StackActionError(self._format_response(status, response_contents)['error'])

    def stack_exists(self, stack_name):
        print 'Checking stack with name: %s' % stack_name
        conn = httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)
        endpoint = "/v1/{tenant_id}/stacks/{stack_name}".format(tenant_id=self.tenant_id, stack_name=stack_name)
        conn.request("GET", endpoint, json.dumps({}), self._headers())
        response = conn.getresponse().status
        conn.close()
        return response == httplib.FOUND

    def get_stack(self, stack_name):
        print 'Fetching stack with name: %s' % stack_name
        conn = httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)
        endpoint = "/v1/{tenant_id}/stacks/{stack_name}".format(tenant_id=self.tenant_id, stack_name=stack_name)
        conn.request("GET", endpoint, json.dumps({}), self._headers())
        response = conn.getresponse()
        if response.status != 302:
            return {'status': response.status}

        stack_location = response.getheader('Location')
        response_contents = response.read()
        conn.close()

        stack_location = stack_location.replace("http://" + self.HEAT_ENDPOINT_URL, "")

        conn2 = httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)

        headers = self._headers()
        headers['Accept'] = "application/vnd.openstack.orchestration-1.0"
        conn2.request("GET", stack_location, None, headers)
        exists_response = conn2.getresponse().read()
        conn2.close()
        stack = json.loads(exists_response)['stack']
        return stack

    @staticmethod
    def _format_response(status, response):
        result = {'status': status}

        if status == httplib.BAD_REQUEST:
            json_response = json.loads(response)
            result.update({'error': json_response['error'], 'explanation': json_response['explanation']})

        return result

    def create_or_update(self, params):
        if not self.stack_exists(params['stack_name']):
            self._create_stack(params)
        else:
            stack = self.get_stack(params['stack_name'])
            self._update_stack(stack['parameters']['OS::stack_id'], params)


if __name__ == "__main__":
    arguments = docopt(__doc__)
    USERNAME = os.environ['OS_USERNAME']
    PASSWORD = os.environ['OS_PASSWORD']
    TENANT_NAME = os.environ['OS_TENANTNAME']
    STACK_NAME = os.environ['HEAT_STACK_NAME']
    ENDPOINT = os.environ['HEAT_ENDPOINT_URL']
    TENANT_ID = os.environ['OS_TENANT_ID']
    IMAGE_ID = os.environ['IMAGE_ID']
    FLOATING_IP_POOL = os.environ['FLOATING_IP_POOL']
    SSH_KEY = os.environ['SSH_KEY']

    user = UserAuth(TENANT_NAME, USERNAME, PASSWORD)

    try:
        token = user.get_token()
    except AuthError:
        print 'Received error when trying to authenticate user: {username}'.format(username=USERNAME)
        raise

    if not '-i' in arguments['-i']:
        if 'APP_INSTANCES' in os.environ:
            arguments['-i'] = os.environ['APP_INSTANCES']
        else:
            arguments['-i'] = 1

    # print Stacks(TENANT_ID, token, ENDPOINT).get_stack('asif_test')

    template = Generator().run(arguments)

    # print template

    params = {
        "stack_name": STACK_NAME,
        "template": template,
        "parameters": {
            "Image_Name": IMAGE_ID,
            "Pool_Name": FLOATING_IP_POOL,
            "SSH_Key": SSH_KEY
        }
    }

    stacks = Stacks(TENANT_ID, token, ENDPOINT)
    stacks.create_or_update(params)
    status = "_IN_PROGRESS"
    while "_IN_PROGRESS" in status:
        time.sleep(3)
        status = stacks.get_stack(params['stack_name'])['stack_status']

    print "Stack status %s" % status

    if "_COMPLETE" in status:
        sys.exit(0)
    sys.exit(1)