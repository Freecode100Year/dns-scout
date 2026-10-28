import unittest
from scout.windows import validate_request

class WindowsValidationTests(unittest.TestCase):
    def test_accept_mixed_families(self):
        validate_request('apply', 2, ['1.1.1.1', '2606:4700:4700::1111'])
    def test_reject_shell_input(self):
        with self.assertRaises(ValueError): validate_request('apply', 2, ['1.1.1.1;whoami'])
    def test_reject_local_address(self):
        with self.assertRaises(ValueError): validate_request('apply', 2, ['127.0.0.1'])
    def test_accept_pair(self):
        self.assertEqual(validate_request('apply', 2, ['1.1.1.1', '8.8.8.8'])['index'], 2)
    def test_restore_without_ips(self):
        self.assertEqual(validate_request('restore', 2, [])['action'], 'restore')

class DualStackTests(unittest.TestCase):
    def test_accept_dual_stack_in_order(self):
        ips = ['8.8.8.8', '1.1.1.1', '2001:4860:4860::8888', '2606:4700:4700::1111']
        self.assertEqual(validate_request('apply', 2, ips)['ips'], ips)

    def test_reject_duplicate(self):
        with self.assertRaises(ValueError):
            validate_request('apply', 2, ['1.1.1.1', '1.1.1.1'])

    def test_reject_three_in_family(self):
        with self.assertRaises(ValueError):
            validate_request('apply', 2, ['1.1.1.1', '8.8.8.8', '9.9.9.9'])

    def test_slots(self):
        from scout.windows import dns_slots
        self.assertEqual(dns_slots(' 8.8.8.8 ', '', '2606:4700:4700::1111', ''), ['8.8.8.8', '2606:4700:4700::1111'])
        for values in [('', '1.1.1.1', '', ''), ('', '', '', '2606:4700:4700::1111'),
                       ('2606:4700:4700::1111', '', '', ''), ('', '', '1.1.1.1', ''), ('', '', '', '')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                dns_slots(*values)
