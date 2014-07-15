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
import httplib
import json
import os.path
import sys
import time
from auth import UserAuth, AuthError
from docopt import docopt

AUTH_ENDPOINT_URL = '10.1.12.16:5000'
NOVA_ENDPOINT_URL = '10.1.12.16:8774'


class HeatTemplate(object):
    def __init__(self, nova_client, template_version, app_script, db_script, instance_count):
        self.nova_client = nova_client
        self.instance_count = instance_count
        self.template_version = template_version
        self.parameters = {}
        self.resources = self.get_resources(app_script, db_script)

    @staticmethod
    def _app_script_block(app_script):
        base_block = {
            'mango_app_script': {
                'type': 'OS::Heat::SoftwareConfig',
                'properties': {
                    'config': ''
                }
            }
        }
        base_block['mango_app_script']['properties']['config'] = '| {script}'.format(script=app_script)

        return base_block

    @staticmethod
    def _db_script_block(db_script):
        base_block = {
            'mango_db_script': {
                'type': 'OS::Heat::SoftwareConfig',
                'properties': {
                    'config': ''
                }
            }
        }
        base_block['mango_db_script']['properties']['config'] = '| {script}'.format(script=db_script)

        return base_block
        # mango_app_script:
        # type: OS::Heat::SoftwareConfig
        # properties:
        # config: |
        # #!/bin/sh
        #       apt-get install -y git
        #       apt-get install -y nodejs-legacy
        #       cd /home/ubuntu
        #       git clone https://github.com/asifrc/meghdoot-test-app.git
        #       meghdoot-test-app/node_modules/.bin/forever start meghdoot-test-app/bin/www
        #       sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000

    def add_parameter(self, parameter):
        self.parameters.update(parameter)
        return self

    def __str__(self):
        namespace = {}
        namespace.update({'heat_template_version': self.template_version})
        namespace.update({'description': 'Heat Template Generated {timestamp}'.format(timestamp=time.strftime("%c"))})

        if self.parameters:
            namespace.update({'parameters': self.parameters})

        namespace.update({'resources': self.resources})

        return json.dumps(namespace, sort_keys=False, indent=4, separators=(',', ': '))

    @staticmethod
    def _flavor():
        return {
            'mango_flavor': {
                'type': 'OS::Nova::Flavor',
                'properties': {
                    'ram': 2048,
                    'vcpus': 1,
                    'disk': 5
                }
            }
        }

    @staticmethod
    def _app_init_block():
        return {
            'mango_app_init': {
                'type': 'OS::Heat::CloudConfig',
                'properties': {
                    'cloud_config': {
                        'users': {
                            'name': 'ubuntu',
                            'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                            'ssh-authorized-keys': {
                                'get_param': 'SSH_Key'
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def _app():
        return {
            "mango_app": {
                "type": "OS::Heat::MultipartMime",
                "properties": {
                    "parts": [
                        {"config": {"get_resource": "mango_app_init"}},
                        {"config": {"get_resource": "mango_db_script"}},
                        {"config": {"get_resource": "mango_app_script"}}
                    ]
                }
            }
        }

    @staticmethod
    def _key_pair():
        return {
            "mango_keypair": {
                "type": "OS::Nova::KeyPair",
                "properties": {
                    "public_key": {
                        "get_param": "SSH_Key"
                    },
                    "name": "mango_from_box1"
                }
            }
        }

    def _key_name(self):
        if self.nova_client.keypair_exists('mango_from_box1'):
            return 'mango_from_box1'
        else:
            return {"get_resource": "mango_keypair"}

    def _app_instance(self, index):
        return {
            "mango_instance_{index}".format(index=index): {
                "depends_on": [
                    "mango_flavor",
                    "mango_keypair"
                ],
                "type": "OS::Nova::Server",
                "properties": {
                    "user_data_format": "RAW",
                    "name": "meghdoot_instance_{index}".format(index=index),
                    "key_name": self._key_name(),
                    "image": {"get_param": "Image_Name"},
                    "user_data": {"get_resource": "mango_app"},
                    "flavor": {"get_resource": "mango_flavor"}
                }
            }
        }

    def get_resources(self, app_script, db_script):
        resources = self._app_init_block()
        resources.update(self._app_script_block(app_script))
        resources.update(self._db_script_block(db_script))
        resources.update(self._app())
        resources.update(self._key_pair())
        resources.update(self._flavor())

        for index in xrange(int(self.instance_count)):
            resources.update(self._app_instance(index + 1))

        return resources


class NovaClient:
    def __init__(self):
        self.username = os.environ['OS_USERNAME']
        self.password = os.environ['OS_PASSWORD']
        self.tenant_name = os.environ['OS_TENANTNAME']
        self.tenant_id = 'a9d08118cbf14b6fbf353f04a3a58704'

    def keypair_exists(self, pair_name):

        user = UserAuth(self.tenant_name, self.username, self.password)

        try:
            token = user.get_token()
        except AuthError:
            print 'Received error when trying to authenticate user: {username}'.format(username=self.username)
            raise

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Auth-Token": token
        }

        conn = httplib.HTTPConnection(NOVA_ENDPOINT_URL)
        endpoint = "/v2/{tenant_id}/os-keypairs/{keypair_name}".format(tenant_id=self.tenant_id, keypair_name=pair_name)
        conn.request("GET", endpoint, json.dumps({}), headers)
        response = conn.getresponse()
        status = response.status
        conn.close()

        return status == 200


class Main(object):
    @staticmethod
    def run(arguments):
        app_script = db_script = ''
        template_version = '2013-05-23'

        parameter = {
            "Pool_Name": {
                "type": "string",
                "label": "Floating IP Pool",
                "description": "my description",
                "default": "asifpub"
            }
        }
        parameter2 = {
            "SSH_Key": {
                'type': 'string',
                'label': 'SSH Key',
                'description': "Public key from the machine from which you'd like to access the instance",
                'default': "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDREkH6Q5tsjPYZ1F9zVTuvOC2zWidftq2ntCw6sLWy9j7sSuHM3mxyP7S5O2oE+pKerBtYieUQDKFo50wB/YRh4BY0aNYSuygQFgjjLDh9IE2HF1JAkfBbRl5rJGVuQtUPUGaldRsZ8KsQauh29jKkFu7N/ZRUI4LrCUb6+pxBt7Np7bNlGxx+5l6EyHkW3kmq5wLEKIYYIqrl71BtMFiFwxHsDpMJonCfKD1aAI0Q+zySJfiAhFkojpLJw7fZhdYTD6B1mDAr5nYKaWcZoG8uuWqJvmlLpcc+oSEnoJMqTVGmVRih1hzXgwRW3Z4vlFqjrQ+p7VnmEuZAwUOJFIgB archoud@thoughtworks.com"
            }
        }
        parameter3 = {
            'Image_Name': {
                'type': 'string',
                'label': 'Image Name or ID',
                'description': 'An Ubuntu Cloud Image image already uploaded to OpenStack',
                'default': 'a2aad0e8-0c68-4eac-a22f-ae23d7cc7bf2'
            }
        }

        with open(arguments['-a'], 'r') as content_file:
            app_script = content_file.read()

        with open(arguments['-b'], 'r') as content_file:
            db_script = content_file.read()

        heat_template = HeatTemplate(NovaClient(), template_version, app_script, db_script, arguments['-i']) \
            .add_parameter(parameter) \
            .add_parameter(parameter2) \
            .add_parameter(parameter3)

        with open(os.path.join(os.path.dirname(sys.argv[0]), 'output.yml'), 'w') as outfile:
            outfile.write(str(heat_template))


if __name__ == "__main__":
    arguments = docopt(__doc__, version='Heat Template Generator 0.1')
    Main.run(arguments)
    print 'Template creation complete'