# Copyright 2014 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

list_services = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'services': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': ['integer', 'string'],
                               'pattern': '^[0-9a-zA-Z_!-]*@[0-9]+$'},
                        'zone': {'type': 'string'},
                        'host': {'type': 'string'},
                        'state': {'type': 'string'},
                        'binary': {'type': 'string'},
                        'status': {'type': 'string'},
                        'updated_at': parameter_types.date_time_or_null,
                        'disabled_reason': {'type': ['string', 'null']}
                    },
                    'additionalProperties': False,
                    'required': ['id', 'zone', 'host', 'state', 'binary',
                                 'status', 'updated_at', 'disabled_reason']
                }
            }
        },
        'additionalProperties': False,
        'required': ['services']
    }
}

enable_disable_service = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'service': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'binary': {'type': 'string'},
                    'host': {'type': 'string'}
                },
                'additionalProperties': False,
                'required': ['status', 'binary', 'host']
            }
        },
        'additionalProperties': False,
        'required': ['service']
    }
}

disable_log_reason = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'service': {
                'type': 'object',
                'properties': {
                    'disabled_reason': {'type': 'string'},
                    'binary': {'type': 'string'},
                    'host': {'type': 'string'},
                    'status': {'type': 'string'}
                },
                'additionalProperties': False,
                'required': ['disabled_reason', 'binary', 'host', 'status']
            }
        },
        'additionalProperties': False,
        'required': ['service']
    }
}
