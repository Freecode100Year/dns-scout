import io
import socket
import threading
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
import dns.message
import dns.rrset
from scout.source import parse_servers, fetch_servers, BASE, PAGES
from scout.i18n import REGIONS
from scout.benchmark import measure, Result, rank_key

class CoreTests(unittest.TestCase):
    def test_localized_region_ids_keep_existing_source_slugs(self):
        expected = {
            'global': '', 'fastest': 'fastest/', 'china': 'china/',
            'hongkong': 'hongkong/', 'taiwan': 'taiwan/', 'japan': 'japan/',
            'singapore': 'singapore/', 'unitedstates': 'unitedstates/', 'germany': 'germany/',
        }
        self.assertEqual({key: PAGES[region['source_key']] for key, region in REGIONS.items()}, expected)

    def test_fetch_summary_keeps_region_url_and_cache_key(self):
        html = '<table><tr><td>1</td><td><span>1.1.1.1</span><br>Cloudflare</td><td><a>Australia</a></td><td>100%</td></tr></table>'
        with tempfile.TemporaryDirectory() as temp:
            with patch('scout.source.urlopen', return_value=io.BytesIO(html.encode('utf-8'))):
                servers, summary = fetch_servers('中国', temp)
            self.assertEqual(servers[0].ip, '1.1.1.1')
            self.assertEqual(summary.mode, 'live')
            self.assertEqual(summary.url, BASE + 'china/')
            self.assertTrue((Path(temp) / 'list-china.json').exists())

    def test_fetch_summary_reports_cache_age_and_error(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'list-china.json'
            path.write_text(json.dumps({'time': 1000, 'servers': [{'ip': '1.1.1.1', 'country': 'Australia', 'provider': 'Cloudflare'}]}), encoding='utf-8')
            with patch('scout.source.urlopen', side_effect=URLError('offline')), patch('scout.source.time.time', return_value=4600):
                servers, summary = fetch_servers('中国', temp)
            self.assertEqual(servers[0].country, 'Australia')
            self.assertEqual(summary.mode, 'cache')
            self.assertEqual(summary.age_hours, 1.0)
            self.assertIn('offline', summary.error)

    def test_source_parses_real_table_shape_and_deduplicates(self):
        row = '<tr><td>1</td><td><span>1.1.1.1</span><br>AS13335 Cloudflare</td><td><a>Australia</a><br>Sydney</td><td>100 % - 4 ms</td></tr>'
        items = parse_servers('<table>'+row+row+'</table>')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].country, 'Australia')
        self.assertEqual(items[0].ip, '1.1.1.1')
    def test_country_page_uses_city_then_plain_country(self):
        html = '<table><tr><td>1</td><td><span>223.5.5.5</span><br>Alibaba</td><td><span>Hangzhou</span><br><span>China</span></td><td>100%</td></tr></table>'
        self.assertEqual(parse_servers(html)[0].country, 'China')

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
