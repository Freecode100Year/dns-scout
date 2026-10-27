import socket
import threading
import unittest
import dns.message
import dns.rrset
from scout.source import parse_servers
from scout.benchmark import measure, Result, rank_key

class CoreTests(unittest.TestCase):
    def test_source_parses_real_table_shape_and_deduplicates(self):
        row = '<tr><td>1</td><td><span>1.1.1.1</span><br>AS13335 Cloudflare</td><td><a>Australia</a><br>Sydney</td><td>100 % - 4 ms</td></tr>'
        items = parse_servers('<table>'+row+row+'</table>')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].country, 'Australia')
        self.assertEqual(items[0].ip, '1.1.1.1')
    def test_bad_source_is_not_silent(self):
        with self.assertRaises(ValueError): parse_servers('<html>blocked</html>')
    def test_rank_prioritizes_reliability(self):
        good = Result('1.1.1.1', [30,40,50], 3)
        bad = Result('8.8.8.8', [1], 3)
        self.assertLess(rank_key(good), rank_key(bad))
    def test_real_udp_query_and_response_validation(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(('127.0.0.1', 0))
        def serve():
            data, peer = server.recvfrom(4096)
            query = dns.message.from_wire(data)
            response = dns.message.make_response(query)
            response.answer.append(dns.rrset.from_text('example.com.', 60, 'IN', 'A', '93.184.215.14'))
            server.sendto(response.to_wire(), peer)
            server.close()
        thread = threading.Thread(target=serve)
        thread.start()
        result = measure('127.0.0.1', ['example.com'], 1, .3, threading.Event(), port=server.getsockname()[1])
        thread.join(2)
        self.assertEqual(result.successes, 1)
        self.assertGreater(result.median_ms, 0)
    def test_timeout_counts_as_failure(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(('127.0.0.1', 0))
        try:
            result = measure('127.0.0.1', ['example.com'], 1, .05, threading.Event(), port=server.getsockname()[1])
            self.assertEqual(result.successes, 0)
            self.assertEqual(result.attempts, 1)
        finally: server.close()
