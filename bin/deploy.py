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

from docopt import docopt

from auth import UserAuth, AuthError
from templatey import Generator


class StackActionError(Exception):
    pass


class Stacks(object):
    HEAT_ENDPOINT_URL = '10.1.12.16:8004'

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
        with closing(httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)) as conn:
            conn.request("POST", "/v1/{tenant_id}/stacks".format(tenant_id=self.tenant_id), json.dumps(params), self._headers())
            response = conn.getresponse()
            response_contents = response.read()
            status = response.status

        return self._format_response(status, response_contents)


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

        return self._format_response(status, response_contents)

    def get_stack(self, stack_name):
        print 'Fetching stack with name: %s' % stack_name
        conn = httplib.HTTPConnection(self.HEAT_ENDPOINT_URL)
        endpoint = "/v1/{tenant_id}/stacks/{stack_name}".format(tenant_id=self.tenant_id, stack_name=stack_name)
        conn.request("GET", endpoint, json.dumps({}), self._headers())
        exists_response = conn.getresponse()
        conn.close()
        return exists_response

    @staticmethod
    def _format_response(status, response):
        result = {'status': status}

        if status == 400:
            json_response = json.loads(response)
            result.update({'error': json_response['error'], 'explanation': json_response['explanation']})

        return result

    def create_or_update(self, params):
        action_response = None
        exists_response = self.get_stack(params['stack_name'])

        if exists_response.status == 404:
            action_response = self._create_stack(params)

        elif exists_response.status == 302:
            stack_id = exists_response.getheader('Location').split('/')[-1]
            action_response = self._update_stack(stack_id, params)

        if action_response['status'] == 400:
            raise StackActionError(action_response['error'])


if __name__ == "__main__":
    arguments = docopt(__doc__)
    USERNAME = os.environ['OS_USERNAME']
    PASSWORD = os.environ['OS_PASSWORD']
    TENANT_NAME = os.environ['OS_TENANTNAME']
    STACK_NAME = os.environ['HEAT_STACK_NAME']
    TENANT_ID = 'a9d08118cbf14b6fbf353f04a3a58704'

    user = UserAuth(TENANT_NAME, USERNAME, PASSWORD)

    try:
        token = user.get_token()
    except AuthError:
        print 'Received error when trying to authenticate user: {username}'.format(username=USERNAME)
        raise

    template = Generator().run(arguments)

    print template

    params = {
        "stack_name": STACK_NAME,
        "template": template
    }

    results = Stacks(TENANT_ID, token).create_or_update(params)

    print "Deployment complete"