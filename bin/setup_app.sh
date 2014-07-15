#!/bin/sh
apt-get install -y git
apt-get install -y nodejs-legacy
cd /home/ubuntu
git clone https://github.com/asifrc/meghdoot-test-app.git
meghdoot-test-app/node_modules/.bin/forever start meghdoot-test-app/bin/www
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 3000