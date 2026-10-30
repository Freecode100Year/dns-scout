import os
import sys
import tempfile
import unittest
import tkinter as tk
import csv

@unittest.skipUnless(sys.platform == 'win32' or os.environ.get('DISPLAY'), 'Needs display')
class UITests(unittest.TestCase):
    def test_english_dns_confirmation_names_preferred_and_alternate_fields(self):
        from scout.app import App
        from unittest.mock import patch
        root = tk.Tk()
        app = None
        try:
            with tempfile.TemporaryDirectory() as temp:
                with patch('scout.app.settings_path', return_value=os.path.join(temp, 'settings.json')):
                    app = App(root)
                    app.set_language('en')
                    app.adapter_map = {'test': {'ifIndex': 2, 'InterfaceGuid': '01234567-89ab-cdef-0123-456789abcdef'}}
                    app.adapter.set('test')
                    app.dns_fields[0].set('8.8.8.8')
                    app.dns_fields[1].set('1.1.1.1')
                    with patch('scout.app.messagebox.askyesno', return_value=False) as ask:
                        app.change('apply')
                    prompt = ask.call_args.args[1]
                    self.assertIn('IPv4 Preferred: 8.8.8.8', prompt)
                    self.assertIn('IPv4 Alternate: 1.1.1.1', prompt)
                    self.assertNotIn('首选', prompt)
        finally:
            app.close() if app else root.destroy()

    def test_close_cancels_pending_poll_callback(self):
        from scout.app import App
        from unittest.mock import patch
        root = tk.Tk()
        app = None
        try:
            with tempfile.TemporaryDirectory() as temp:
                with patch('scout.app.settings_path', return_value=os.path.join(temp, 'settings.json')):
                    app = App(root)
                    callback = root.tk.splitlist(root.tk.call('after', 'info'))[0]
                    with patch.object(root, 'destroy'):
                        app.close()
                    with self.assertRaises(tk.TclError):
                        root.tk.call('after', 'info', callback)
        finally:
            app.close() if app else root.destroy()

    def test_csv_headers_follow_language_and_metadata_is_safe(self):
        from scout.app import App
        from scout.source import Server
        from scout.benchmark import Result
        from unittest.mock import patch
        root = tk.Tk()
        app = None
        try:
            with tempfile.TemporaryDirectory() as temp:
                with patch('scout.app.settings_path', return_value=os.path.join(temp, 'settings.json')):
                    app = App(root)
                    app.servers = [Server('1.1.1.1', '=Australia', '+Cloudflare')]
                    app.results = [Result('1.1.1.1', [10,20,30], 3, '已取消')]
                    app.set_language('zh-CN')
                    chinese_path = os.path.join(temp, 'zh.csv')
                    app.write_csv(chinese_path)
                    app.set_language('en')
                    english_path = os.path.join(temp, 'en.csv')
                    app.write_csv(english_path)
                with open(chinese_path, encoding='utf-8-sig', newline='') as handle:
                    chinese_rows = list(csv.reader(handle))
                with open(english_path, encoding='utf-8-sig', newline='') as handle:
                    english_rows = list(csv.reader(handle))
                self.assertEqual(chinese_rows[0][:3], ['DNS', '地区', '运营商'])
                self.assertEqual(english_rows[0][:3], ['DNS address', 'Region', 'Provider'])
                self.assertEqual(english_rows[1][1:3], ["'=Australia", "'+Cloudflare"])
                self.assertEqual(english_rows[1][8], '已取消')
        finally:
            app.close() if app else root.destroy()

    def test_language_switch_preserves_live_ui_state(self):
        from scout.app import App
        from scout.source import Server
        from scout.benchmark import Result
        from unittest.mock import patch
        root = tk.Tk()
        app = None
        try:
            with tempfile.TemporaryDirectory() as temp:
                preference = os.path.join(temp, 'settings.json')
                with patch('scout.app.settings_path', return_value=preference):
                    app = App(root)
                    app.servers = [Server('1.1.1.1', 'Australia', 'Cloudflare')]
                    app.results = [Result('1.1.1.1', [10,20,30], 3)]
                    app.render()
                    app.set_language('zh-CN')
                    app.family_id = 'ipv6'
                    app.region.set('中国')
                    app.on_region_selected()
                    self.assertEqual(app.region_id, 'china')
                    app.domains.set('example.org')
                    app.dns_fields[0].set('8.8.8.8')
                    app.table.selection_set('1.1.1.1')

                    app.set_language('en')
                    root.update()
                    self.assertEqual(app.table.heading('ip', 'text'), 'DNS address')
                    self.assertEqual(app.start_button.cget('text'), 'Find best DNS')
                    self.assertEqual(app.region_id, 'china')
                    self.assertEqual(app.region.get(), 'China')
                    self.assertEqual(app.family_id, 'ipv6')
                    self.assertEqual(app.domains.get(), 'example.org')
                    self.assertEqual(app.dns_fields[0].get(), '8.8.8.8')
                    self.assertEqual(app.table.selection(), ('1.1.1.1',))
                    self.assertEqual(len(app.table.get_children()), 1)

                    app.set_language('zh-CN')
                    root.update()
                    self.assertEqual(app.table.heading('ip', 'text'), 'DNS 地址')
                    self.assertEqual(app.start_button.cget('text'), '开始优选')
                    self.assertEqual(app.region.get(), '中国')
                    self.assertEqual(json_read(preference), 'zh-CN')
        finally:
            app.close() if app else root.destroy()

    def test_construct_render_select_export_and_close(self):
        from scout.app import App
        from scout.source import Server
        from scout.benchmark import Result
        root = tk.Tk()
        app = None
        try:
            app = App(root)
            app.servers = [Server('1.1.1.1', 'Australia', 'Cloudflare')]
            app.results = [Result('1.1.1.1', [10,20,30], 3)]
            app.render()
            root.update()
            self.assertEqual(len(app.table.get_children()), 1)
            app.table.selection_set('1.1.1.1')
            self.assertEqual(app.selected_ips(), ['1.1.1.1'])
            app.dns_fields[1].set('8.8.8.8')
            app.dns_fields[2].set('2606:4700:4700::1111')
            app.fill_dns()
            self.assertEqual([field.get() for field in app.dns_fields], ['1.1.1.1', '', '2606:4700:4700::1111', ''])
            from unittest.mock import patch
            app.adapter_map = {'test': {'ifIndex': 2, 'InterfaceGuid': '01234567-89ab-cdef-0123-456789abcdef'}}
            app.adapter.set('test')
            app.dns_fields[0].set('8.8.8.8')
            app.dns_fields[1].set('1.1.1.1')
            with patch('scout.app.messagebox.askyesno', return_value=True), patch('scout.app.windows.configure', return_value='ok') as configure, patch.object(app, 'background', side_effect=lambda job: job()):
                app.change('apply')
                self.assertEqual(configure.call_args.args[2], ['8.8.8.8', '1.1.1.1', '2606:4700:4700::1111'])
            app.set_busy(True)
            app.set_busy(False)
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, 'results.csv')
                app.write_csv(path)
                with open(path, encoding='utf-8-sig') as f:
                    self.assertIn('1.1.1.1', f.read())
        finally:
            app.close() if app else root.destroy()


def json_read(path):
    import json
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)['language']
