#!/bin/sh

echo Checking out $BRANCH in cinder...
cd /opt/stack/cinder
git pull
echo Checking out $BRANCH in glance...
cd /opt/stack/glance
git pull
echo Checking out $BRANCH in heat...
cd /opt/stack/heat
git pull
echo Checking out $BRANCH in horizon...
cd /opt/stack/horizon
git pull
echo Checking out $BRANCH in keystone...
cd /opt/stack/keystone
git pull
echo Checking out $BRANCH in nova...
cd /opt/stack/nova
git pull
