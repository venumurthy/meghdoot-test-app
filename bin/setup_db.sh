#!/bin/sh
apt-get install -y mongodb-server
sed -i 's/127.0.0.1/0.0.0.0/g' /etc/mongodb.conf
sudo service mongodb restart
