# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

import testtools

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import test

CONF = config.CONF


class ServerTest(base.BaseV2ComputeTest):
    disk_config = 'AUTO'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(ServerTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServerTest, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()
        super(ServerTest, cls).resource_setup()

    # NOTE(jake): Booting an instance should really be in resource_setup()
    # but we want to get the time taken to boot an instance, so we are
    # booting it in a test.
    # The downside is that you CANNOT have any other test here that depends on
    # cls.server, because that will fail if that test runs before this.
    @test.idempotent_id('516361c3-c128-410d-b25c-7a70b5f4c3b5')
    @testtools.skipUnless(CONF.validation.run_validation,
                          'Instance validation tests are disabled.')
    def test_boot_server(self):
        # Boots server
        self.meta = {'scenario': 'nectar'}
        self.name = data_utils.rand_name('server')
        self.password = data_utils.rand_password()
        disk_config = self.disk_config
        self.server_initial = self.create_test_server(
            validatable=True,
            wait_until='ACTIVE',
            name=self.name,
            metadata=self.meta,
            disk_config=disk_config,
            adminPass=self.password)
        self.server = (self.client.show_server(self.server_initial['id'])
                       ['server'])

        # Basic verification
        linux_client = remote_client.RemoteClient(
            self.get_server_ip(self.server),
            self.ssh_user,
            self.password,
            self.validation_resources['keypair']['private_key'],
            server=self.server,
            servers_client=self.client)

        # Verify that the number of vcpus reported by the instance matches
        # the amount stated by the flavor
        flavor = self.flavors_client.show_flavor(self.flavor_ref)['flavor']
        self.assertEqual(flavor['vcpus'], linux_client.get_number_of_vcpus())

        # Verify the instance host name is the same as the server name
        self.assertTrue(linux_client.hostname_equals_servername(self.name))
