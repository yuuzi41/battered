# Copyright (c) 2018 Yuji Hagiwara
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import json
from datetime import datetime

class BatteredMiddleware(object):
    """
    """

    def __init__(self, app, conf):
        self.app = app
        self.logger = logging.getLogger('BatteredMiddleware')
        self.tenants = [
            {
                'name': 'demo',
                'id': 'b76476eb-647b-4f00-bb10-9368803a372d',
                'users': [
                    {
                        'name': 'testname',
                        'username': 'test',
                        'password': 'pass',
                        'token': 'TOKEN'
                    },
                    {
                        'name': 'Demo User',
                        'username': 'demo',
                        'password': 'secretsecret',
                        'token': 'DEMOTOKEN'
                    }
                ],
                'url': "http://10.0.0.1:8080/v1/AUTH_fc394f2ab2df4114bde39905f800dc57"
            }
        ]

    def __call__(self, env, start_response):
        self.logger.info('call')

        if not env['PATH_INFO'].startswith("/v2.0/tokens"):
            return self.app(env, start_response)

        if env['REQUEST_METHOD'] != "POST":
            # return 405 if method isn't POST
            start_response('405 Method Not Allowed', [('Content-Type', 'application/json')])
            return [json.dumps({}).encode()]

        # the environment variable CONTENT_LENGTH may be empty or missing
        try:
            request_body_size = int(env.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        # read requst body
        request_body = env['wsgi.input'].read(request_body_size)
        if env['CONTENT_TYPE'] == "application/json":
            req = json.loads(request_body)
            if 'auth' in req:
                if 'tenantId' in req['auth']:
                    tenant_id = req['auth']['tenantId']
                    tenant = [t for t in self.tenants if t['id'] == tenant_id]
                elif 'tenantName' in req['auth']:
                    tenant_name = req['auth']['tenantName']
                    tenant = [t for t in self.tenants if t['name'] == tenant_name]
                else:
                    # return 400 if both tenantId and tenantName aren't provided.
                    self.logger.info("Neither tenantId nor tenantName are provided.")
                    start_response('400 Bad Request', [('Content-Type', 'application/json')])
                    return [json.dumps({}).encode()]

                if len(tenant) != 1:
                    self.logger.info("tenant")
                    # return 401 if Tenant is not valid.
                    start_response('401 Unauthorized', [('Content-Type', 'application/json')])
                    return [json.dumps({}).encode()]

                # tenant must be 1-element list, so get an element.
                tenant = tenant[0]

                if 'passwordCredentials' in req['auth']:
                    username = req['auth']['passwordCredentials']['username']
                    password = req['auth']['passwordCredentials']['password']
                    user = [u for u in tenant['users'] if u['username'] == username and u['password'] == password]
                elif 'token' in req['auth']:
                    token = req['auth']['token']
                    user = [u for u in tenant['users'] if u['token'] == token]
                else:
                    # return 400 if both token and credentials aren't provided.
                    start_response('400 Bad Request', [('Content-Type', 'application/json')])
                    return [json.dumps({}).encode()]

                if len(user) != 1:
                    # return 401 if Tenant is not valid.
                    start_response('401 Unauthorized', [('Content-Type', 'application/json')])
                    return [json.dumps({}).encode()]

                # user must be 1-element list, so get an element.
                user = user[0]

        else:
            # todo: support other formats such as xml
            start_response('401 Unauthorized', [('Content-Type', 'application/json')])
            return [json.dumps({}).encode()]

        # create a response
        res = {'access': {
            'token': {}, 
            'user': {},
            'serviceCatalog': [],
            'metadata': {'is_admin': 0, 'roles': []},
            }}
        res['access']['token'] = {
            'issued_at': datetime.utcnow().isoformat(),
            'expires': "2099-12-31T23:59:59Z",
            'id': "aaaaa-bbbbb-ccccc-dddd", #forever
            'tenant': {
                "description": None,
                "enabled": True,
                "id": tenant['id'],
                "name": tenant['name']
            }
        }
        res['access']['user'] = {
            'id': "",
            'username': user['username'],
            'name': user['name'],
            'roles': [],
            'roles_links': []
        }
        res['access']['serviceCatalog'].append({
            "endpoints": [
                {
                    "adminURL": tenant['url'], #admin isn't required for Swift
                    "id": "16b76b5e5b7d48039a6e4cc3129545f3",
                    "region": "RegionOne",
                    "internalURL": tenant['url'],
                    "publicURL": tenant['url'] # I'm not sure whether internalURL and publicURL should be same or not.
                }
            ],
            "endpoints_links": [],
            "type": "object-store",
            "name": "swift"
        })
        
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(res).encode()]

 
