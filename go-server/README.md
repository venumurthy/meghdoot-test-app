To bring up a Go server on the AWS using the CloudFormation Template

use this command on the aws CLI to bring up the Go infra

    aws cloudformation create-stack --stack-name meghdoot-go --template-body 'file://./infrastructure-template.json' --capabilities CAPABILITY_IAM

Two instances one of which is the Go Master and Agent is created

    aws cloudformation describe-stacks


CAPABILITIES  CAPABILITY_IAM
OUTPUTS CIMasterPublicIp  54.152.177.253
OUTPUTS CISlavePublicIp 54.86.41.58
OUTPUTS CIMasterPrivateIp 10.0.0.195

put these values into the inventory file

and run ansible-playbook playbook.yml -u ubuntu -i inventory --private-key="~/.ssh/venu.pem"

ssh tunnel into the Go servers port

    ssh -L 8153:localhost:8153 ubuntu@54.152.177.253 -i ~/.ssh/venu.pem

access the go server from 

localhost:8153

Go to the /etc for the crusie-config.xml and copy the contents of this file.

Go to the "Admin" ==> "Config XML" ==> "Edit" paste the content. 



