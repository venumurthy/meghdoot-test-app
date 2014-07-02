export BRANCH=master

cd /opt/stack/cinder
git checkout $BRANCH
cd /opt/stack/glance
git checkout $BRANCH
cd /opt/stack/heat
git checkout $BRANCH
cd /opt/stack/horizon
git checkout $BRANCH
cd /opt/stack/keystone
git checkout $BRANCH
cd /opt/stack/nova
git checkout $BRANCH


#cd /opt/stack/cinder
#cd /opt/stack/glance
#cd /opt/stack/heat
#cd /opt/stack/horizon
#cd /opt/stack/keystone
#cd /opt/stack/nova
