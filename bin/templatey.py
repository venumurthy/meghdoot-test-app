# -*- coding: utf-8 -*-

"""Heat Template Generator

Usage:
  templatey.py [-i=<instance_count>] -a=<app_setup_script_path> -b=<db_setup_script_path> [-s=<save_file>]
  templatey.py (-h | --help)
  templatey.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  -i=<instance_count>          Number of instances [default: 1].
  -a=<app_setup_script_path>       Path to the application setup script.
  -b=<db_setup_script_path>       Path to the database setup script.
  -s=<save_file>            Save the template output to a file [default: false]

"""
import httplib
import json
import os.path
import sys
import time
from docopt import docopt
from contextlib import closing

from auth import UserAuth, AuthError


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
        # apt-get install -y git
        #       apt-get install -y nodejs-legacy
        #       cd /home/ubuntu
        #       git clone https://github.com/asifrc/meghdoot-test-app.git
        #       meghdoot-test-app/node_modules/.bin/forever start meghdoot-test-app/bin/www
        #       sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000

    def add_parameter(self, parameter):
        self.parameters.update(parameter)
        return self

    @staticmethod
    def _flavor():
        return {
            'flavor': {
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
    def _application_parts():
        return {
            "application_parts": {
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
    def _db_configuration():
        db_resource = {
            "database_parts": {
                "type": "OS::Heat::MultipartMime",
                "properties": {
                    "parts": [
                        {"config": {"get_resource": "mango_app_init"}},
                        {"config": {"get_resource": "mango_db_script"}}
                    ]
                }
            }
        }

        db_resource.update({
            "database_instance": {
                "depends_on": [
                    "flavor",
                    "keypair"
                ],
                "type": "OS::Nova::Server",
                "properties": {
                    "user_data_format": "RAW",
                    "name": "database_instance",
                    "key_name": {
                        "get_resource": "keypair"
                    },
                    "image": {"get_param": "Image_Name"},
                    "user_data": {"get_resource": "database_parts"},
                    "flavor": {"get_resource": "flavor"}
                }
            }
        })
        return db_resource

    @staticmethod
    def _key_pair():
        return {
            'keypair': {
                "type": "OS::Nova::KeyPair",
                "properties": {
                    "public_key": {
                        "get_param": "SSH_Key"
                    },
                    "name": "mango_from_box1"
                }
            }
        }

    @staticmethod
    def _key_name(keypair_exists):
        if keypair_exists:
            return 'mango_from_box1'
        else:
            return {"get_resource": "keypair"}

    def _app_instance(self, index, keypair_exists):
        return {
            "app_instance_{index}".format(index=index): {
                "depends_on": ["flavor", "keypair"],
                "type": "OS::Nova::Server",
                "properties": {
                    "user_data_format": "RAW",
                    "name": "app_instance_{index}".format(index=index),
                    "key_name": self._key_name(keypair_exists),
                    "image": {"get_param": "Image_Name"},
                    "user_data": {"get_resource": "application_parts"},
                    "flavor": {"get_resource": "flavor"}
                }
            }
        }

    def get_resources(self, app_script, db_script):
        keypair_exists = self.nova_client.keypair_exists('mango_from_box1')

        resources = self._app_init_block()
        resources.update(self._app_script_block(app_script))
        resources.update(self._db_script_block(db_script))
        resources.update(self._application_parts())
        resources.update(self._db_configuration())
        resources.update(self._flavor())
        resources.update(self._floating_ip_resource())

        if not keypair_exists:
            resources.update(self._key_pair())

        for index in xrange(int(self.instance_count)):
            resources.update(self._app_instance(index + 1, keypair_exists))

        return resources

    def _floating_ip_resource(self):

        ip_resources = {}
        for index in xrange(int(self.instance_count)):
            resource_name = "app_instance_{index}".format(index=index + 1)
            ip_name = "mango_floatingip_{index}".format(index=index + 1)
            ip_resources.update({
                ip_name: {
                    "type": "OS::Nova::FloatingIP",
                    "properties": {
                        "pool": {
                            "get_param": "Pool_Name"
                        }
                    }
                }
            })
            ip_resources.update({
                "mango_ip_assoc{index}".format(index=index + 1): {
                    "depends_on": [
                        resource_name
                    ],
                    "type": "OS::Nova::FloatingIPAssociation",
                    "properties": {
                        "server_id": {
                            "get_resource": resource_name
                        },
                        "floating_ip": {
                            "get_resource": ip_name
                        }
                    }
                }
            })
        return ip_resources

    def __str__(self):
        namespace = {}
        namespace.update({'heat_template_version': self.template_version})
        namespace.update({'description': 'Heat Template Generated {timestamp}'.format(timestamp=time.strftime("%c"))})

        if self.parameters:
            namespace.update({'parameters': self.parameters})

        namespace.update({'resources': self.resources})

        return json.dumps(namespace, sort_keys=False, indent=4, separators=(',', ': '))


class NovaClient(object):
    NOVA_ENDPOINT_URL = '10.1.12.16:8774'

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

        with closing(httplib.HTTPConnection(self.NOVA_ENDPOINT_URL)) as conn:
            endpoint = "/v2/{tenant_id}/os-keypairs/{keypair_name}".format(tenant_id=self.tenant_id,
                                                                           keypair_name=pair_name)
            conn.request("GET", endpoint, json.dumps({}), headers)
            response = conn.getresponse()
            status = response.status

        return status == 200


class Generator(object):
    def run(self, arguments):
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

        app_script = self._script_contents(arguments['-a'])
        db_script = self._script_contents(arguments['-b'])

        heat_template = HeatTemplate(NovaClient(), template_version, app_script, db_script, arguments['-i']) \
            .add_parameter(parameter) \
            .add_parameter(parameter2) \
            .add_parameter(parameter3)

        if '-s' in arguments and arguments['-s'] is True:
            self.save(heat_template)

        return str(heat_template)

    def _script_contents(self, script_path):
        with open(script_path, 'r') as content_file:
            return content_file.read().replace('\n', ' && ')

    @staticmethod
    def save(heat_template):
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'hot_generated.json'), 'w') as outfile:
            outfile.write(str(heat_template))


if __name__ == "__main__":
    arguments = docopt(__doc__, version='Heat Template Generator 0.1')
    Generator().run(arguments)
    print 'Template creation complete'
