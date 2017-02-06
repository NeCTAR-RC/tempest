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

from tempest.api.orchestration import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class TestServerStackLimits(base.BaseOrchestrationTest):

    @decorators.idempotent_id('ec9bed71-c460-45c9-ab98-295caa9fd76b')
    def test_exceed_max_template_size_fails(self):
        stack_name = data_utils.rand_name('heat')
        fill = 'A' * CONF.orchestration.max_template_size
        template = '''
HeatTemplateFormatVersion: '2012-12-12'
Description: '%s'
Outputs:
  Foo: bar''' % fill
        ex = self.assertRaises(lib_exc.BadRequest, self.create_stack,
                               stack_name, template)
        self.assertIn('exceeds maximum allowed size', str(ex))

    @decorators.idempotent_id('d1b83e73-7cad-4a22-9839-036548c5387c')
    def test_exceed_max_resources_per_stack(self):
        stack_name = data_utils.rand_name('heat')
        # Create a big template, one resource more than the limit
        template = 'heat_template_version: \'2013-05-23\'\nresources:\n'
        rsrc_snippet = '  random%s:\n    type: \'OS::Heat::RandomString\'\n'
        num_resources = CONF.orchestration.max_resources_per_stack + 1
        for i in range(num_resources):
            template += rsrc_snippet % i

        ex = self.assertRaises(lib_exc.BadRequest, self.create_stack,
                               stack_name, template)
        self.assertIn('Maximum resources per stack exceeded', str(ex))
