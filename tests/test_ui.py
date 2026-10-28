import os
import sys
import tempfile
import unittest
import tkinter as tk

@unittest.skipUnless(sys.platform == 'win32' or os.environ.get('DISPLAY'), 'Needs display')
class UITests(unittest.TestCase):
    def test_construct_render_select_export_and_close(self):
        from scout.app import App
        from scout.source import Server
        from scout.benchmark import Result
        root = tk.Tk()
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
        finally: root.destroy()
