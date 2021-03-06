#    Copyright 2015 Hewlett-Packard Development Company, L.P.
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

from unittest import mock

from octavia.cmd import house_keeping
from octavia.tests.unit import base


class TestHouseKeepingCMD(base.TestCase):
    def setUp(self):
        super().setUp()

    @mock.patch('octavia.cmd.house_keeping.db_cleanup_thread_event')
    @mock.patch('octavia.controller.housekeeping.'
                'house_keeping.DatabaseCleanup')
    def test_db_cleanup(self, mock_DatabaseCleanup,
                        db_cleanup_event_mock):
        db_cleanup = mock.MagicMock()
        delete_old_amphorae = mock.MagicMock()
        db_cleanup.delete_old_amphorae = delete_old_amphorae
        mock_DatabaseCleanup.return_value = db_cleanup

        # mock db_cleanup_thread_event.is_set() in the while loop
        db_cleanup_event_mock.is_set = mock.MagicMock()
        db_cleanup_event_mock.is_set.side_effect = [False, Exception('break')]

        self.assertRaisesRegex(Exception, 'break', house_keeping.db_cleanup)

        mock_DatabaseCleanup.assert_called_once_with()
        self.assertEqual(1, db_cleanup.delete_old_amphorae.call_count)

    @mock.patch('octavia.cmd.house_keeping.cert_rotate_thread_event')
    @mock.patch('octavia.controller.housekeeping.'
                'house_keeping.CertRotation')
    def test_hk_cert_rotation_with_exception(self, mock_CertRotation,
                                             cert_rotate_event_mock):
        # mock cert_rotate object
        cert_rotate_mock = mock.MagicMock()
        # mock rotate()
        rotate_mock = mock.MagicMock()

        cert_rotate_mock.rotate = rotate_mock

        mock_CertRotation.return_value = cert_rotate_mock

        # mock cert_rotate_thread_event.is_set() in the while loop
        cert_rotate_event_mock.is_set = mock.MagicMock()
        cert_rotate_event_mock.is_set.side_effect = [False, Exception('break')]

        self.assertRaisesRegex(Exception, 'break',
                               house_keeping.cert_rotation)

        mock_CertRotation.assert_called_once_with()
        self.assertEqual(1, cert_rotate_mock.rotate.call_count)

    @mock.patch('octavia.cmd.house_keeping.cert_rotate_thread_event')
    @mock.patch('octavia.controller.housekeeping.'
                'house_keeping.CertRotation')
    def test_hk_cert_rotation_without_exception(self, mock_CertRotation,
                                                cert_rotate_event_mock):
        # mock cert_rotate object
        cert_rotate_mock = mock.MagicMock()
        # mock rotate()
        rotate_mock = mock.MagicMock()

        cert_rotate_mock.rotate = rotate_mock

        mock_CertRotation.return_value = cert_rotate_mock

        # mock cert_rotate_thread_event.is_set() in the while loop
        cert_rotate_event_mock.is_set = mock.MagicMock()
        cert_rotate_event_mock.is_set.side_effect = [False, True]

        self.assertIsNone(house_keeping.cert_rotation())

        mock_CertRotation.assert_called_once_with()
        self.assertEqual(1, cert_rotate_mock.rotate.call_count)

    @mock.patch('octavia.cmd.house_keeping.cert_rotate_thread_event')
    @mock.patch('octavia.cmd.house_keeping.db_cleanup_thread_event')
    @mock.patch('threading.Thread')
    @mock.patch('octavia.common.service.prepare_service')
    def test_main(self, mock_service, mock_thread,
                  db_cleanup_thread_event_mock,
                  cert_rotate_thread_event_mock):

        db_cleanup_thread_mock = mock.MagicMock()
        cert_rotate_thread_mock = mock.MagicMock()

        mock_thread.side_effect = [db_cleanup_thread_mock,
                                   cert_rotate_thread_mock]

        db_cleanup_thread_mock.daemon.return_value = True
        cert_rotate_thread_mock.daemon.return_value = True

        house_keeping.main()

        db_cleanup_thread_mock.start.assert_called_once_with()
        cert_rotate_thread_mock.start.assert_called_once_with()

        self.assertTrue(db_cleanup_thread_mock.daemon)
        self.assertTrue(cert_rotate_thread_mock.daemon)

    @mock.patch('octavia.cmd.house_keeping.cert_rotate_thread_event')
    @mock.patch('octavia.cmd.house_keeping.db_cleanup_thread_event')
    @mock.patch('threading.Thread')
    @mock.patch('octavia.common.service.prepare_service')
    def test_main_keyboard_interrupt(self, mock_service, mock_thread,
                                     db_cleanup_thread_event_mock,
                                     cert_rotate_thread_event_mock):
        db_cleanup_thread_mock = mock.MagicMock()
        cert_rotate_thread_mock = mock.MagicMock()

        mock_thread.side_effect = [db_cleanup_thread_mock,
                                   cert_rotate_thread_mock]

        db_cleanup_thread_mock.daemon.return_value = True
        cert_rotate_thread_mock.daemon.return_value = True

        mock_join = mock.MagicMock()
        mock_join.side_effect = [KeyboardInterrupt, None]
        db_cleanup_thread_mock.join = mock_join

        house_keeping.main()

        db_cleanup_thread_event_mock.set.assert_called_once_with()

        cert_rotate_thread_event_mock.set.assert_called_once_with()

        db_cleanup_thread_mock.start.assert_called_once_with()
        cert_rotate_thread_mock.start.assert_called_once_with()

        self.assertTrue(db_cleanup_thread_mock.daemon)
        self.assertTrue(cert_rotate_thread_mock.daemon)
        self.assertEqual(2, db_cleanup_thread_mock.join.call_count)
        cert_rotate_thread_mock.join.assert_called_once_with()

    @mock.patch('oslo_config.cfg.CONF.mutate_config_files')
    def test_mutate_config(self, mock_mutate):
        house_keeping._mutate_config()

        mock_mutate.assert_called_once()
