#!/bin/bash

token_response=$(curl -i -X POST http://10.1.12.16:5000/v2.0/tokens -H "Content-Type: application/json" -H "Accept: application/json" -H "User-Agent: python-keystoneclient" -d '{"auth": {"tenantName": "admin", "passwordCredentials": {"username": "admin", "password": "nomoresecrete"}}}')

# echo "$token_response"
# export TENANT_ID=0072d3db63ac4a1c8a73c1a74eb42ef4​
#export URL= /v1/0072d3db63ac4a1c8a73c1a74eb42ef4​/stacks

# http://10.1.12.16:8004/v1/0072d3db63ac4a1c8a73c1a74eb42ef4/stacks

# asdf = $(curl -i -X http://10.1.12.16:8004/v1/​0072d3db63ac4a1c8a73c1a74eb42ef4​/stacks)

# -H  "X-Auth-Token: $token_response"
echo token_response| jq '.id'
# curl -i -X GET http://10.1.12.16:8004/v1/​ -H  "X-Auth-Token: $token_response"

# echo "$URL"