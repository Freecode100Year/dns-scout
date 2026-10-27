import unittest
from scout.windows import validate_request

class WindowsValidationTests(unittest.TestCase):
    def test_reject_mixed_families(self):
        with self.assertRaises(ValueError): validate_request('apply', 2, ['1.1.1.1', '2606:4700:4700::1111'])
    def test_reject_shell_input(self):
        with self.assertRaises(ValueError): validate_request('apply', 2, ['1.1.1.1;whoami'])
    def test_reject_local_address(self):
        with self.assertRaises(ValueError): validate_request('apply', 2, ['127.0.0.1'])
    def test_accept_pair(self):
        self.assertEqual(validate_request('apply', 2, ['1.1.1.1', '8.8.8.8'])['index'], 2)
    def test_restore_without_ips(self):
        self.assertEqual(validate_request('restore', 2, [])['action'], 'restore')
