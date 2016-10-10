# Copyright 2013 NEC Corporation
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

from tempest.common import custom_matchers
from tempest.common import waiters
from tempest import config
from tempest import exceptions
from tempest.lib import exceptions as lib_exc
from tempest.common.utils import data_utils
from tempest.scenario import manager
from tempest import test

CONF = config.CONF


class TestCommunityImage(manager.ScenarioTest):

    """This is a basic scenario test for checking Community Images.

    This test below:
    * across the multiple components
    * as a regular user
    * with and without optional parameters
    * check command outputs

    Steps:
    1. Check Metadata (test metadata function)
    2. Create keypair
    3. Boot instance with keypair and get list of instances
    4. Check SSH connection to instance
    5. Run diagnostic tests on instance
    6. Reboot instance
    7. Check SSH connection to instance after reboot

    """

    def nova_list(self):
        servers = self.servers_client.list_servers()
        # The list servers in the compute client is inconsistent...
        return servers['servers']

    def nova_show(self, server):
        got_server = (self.servers_client.show_server(server['id'])
                      ['server'])
        excluded_keys = ['OS-EXT-AZ:availability_zone']
        # Exclude these keys because of LP:#1486475
        excluded_keys.extend(['OS-EXT-STS:power_state', 'updated'])
        self.assertThat(
            server, custom_matchers.MatchesDictExceptForKeys(
                got_server, excluded_keys=excluded_keys))

    def nova_reboot(self, server):
        self.servers_client.reboot_server(server['id'], type='SOFT')
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

    def create_and_add_security_group_to_server(self, server):
        secgroup = self._create_security_group()
        self.servers_client.add_security_group(server['id'],
                                               name=secgroup['name'])
        self.addCleanup(self.servers_client.remove_security_group,
                        server['id'], name=secgroup['name'])

        def wait_for_secgroup_add():
            body = (self.servers_client.show_server(server['id'])
                    ['server'])
            return {'name': secgroup['name']} in body['security_groups']

        if not test.call_until_true(wait_for_secgroup_add,
                                    CONF.compute.build_timeout,
                                    CONF.compute.build_interval):
            msg = ('Timed out waiting for adding security group %s to server '
                   '%s' % (secgroup['id'], server['id']))
            raise exceptions.TimeoutException(msg)


    @test.idempotent_id('bdbb5441-9204-419d-a225-b4fdbfb1a1a8')
    @test.services('compute', 'network')
    def test_community_image(self):

        # Get the image ID
        image_id = CONF.compute.image_ref
        
        # Get the image info
        # whilst validating against the 
        # community image schema
        info = self.community_image_client.show_image(image_id)

        linux_user = info['default_user']

        keypair = self.create_keypair()

        server = self.create_server(image_id=CONF.compute.image_ref,
                                    key_name=keypair['name'],
                                    wait_until='ACTIVE')
        servers = self.nova_list()
        self.assertIn(server['id'], [x['id'] for x in servers])

        self.nova_show(server)
        ip = self.get_server_ip(server)
        self.create_and_add_security_group_to_server(server)

        # check that we can SSH to the server before reboot
        self.linux_client = self.get_remote_client(
            ip, username=linux_user, private_key=keypair['private_key'])

        # Check that ephemeral disk is ext4 and read-write mounted on vdb
        self.linux_client.exec_command("""
                                grep '/dev/vdb.*ext4.*rw' /proc/mounts""")

        # Check that none/noop I/O scheduler in use
        sched = self.linux_client.exec_command("""
                                ! grep -Ev '(none|\[noop\])' /sys/block/*/queue/scheduler""")
        
        # Check Root filesystem is resized
        self.linux_client.exec_command("""
                                df -P -BG / | sed -n -e 's/^\/\s\+\([0-9]\+\)G.*/\1/p'\
                                || test $? -gt 4""")
        
        # Check if kernel console log configured correctly
        self.linux_client.exec_command("""
                                grep 'console=tty0 console=ttyS0,115200n8' /proc/cmdline""")

        # Check that default route via interface named eth0
        self.linux_client.exec_command("""
                                /sbin/ip route | grep -E 'default via .* dev eth0'""")

        # Check that no default passwords exist
        self.linux_client.exec_command("""
                                test "$(sudo cut -d ':' -f 2 /etc/shadow | cut -d '$' -sf3)" = "" """)

        # Check if NTP or chrony service is running
        self.linux_client.exec_command(""" pgrep 'ntp|chronyd'""")

        # Check if single SSH authorized key for root exists
        rootkey = str(self.linux_client.exec_command("""sudo wc -l /root/.ssh/authorized_keys | cut -d ' ' -f1"""))
        self.assertEqual('1', rootkey.strip())

        # Check if single SSH authorized key for current user exists
        userkey = str(self.linux_client.exec_command("""wc -l ~/.ssh/authorized_keys | cut -d ' ' -f1"""))
        self.assertEqual('1', userkey.strip())

        self.nova_reboot(server)

        # check that we can SSH to the server after reboot
        # (both connections are part of the scenario)
        self.linux_client = self.get_remote_client(
            ip, username=linux_user, private_key=keypair['private_key'])
