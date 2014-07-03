#!/bin/sh

#cinder
#glance
#heat
#horizon
#keystone
#nova

export BRANCH=master

echo Checking out $BRANCH in cinder...
cd /opt/stack/cinder
git checkout $BRANCH
echo Checking out $BRANCH in glance...
cd /opt/stack/glance
git checkout $BRANCH
echo Checking out $BRANCH in heat...
cd /opt/stack/heat
git checkout $BRANCH
echo Checking out $BRANCH in horizon...
cd /opt/stack/horizon
git checkout $BRANCH
echo Checking out $BRANCH in keystone...
cd /opt/stack/keystone
git checkout $BRANCH
echo Checking out $BRANCH in nova...
cd /opt/stack/nova
git checkout $BRANCH
