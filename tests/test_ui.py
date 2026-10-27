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
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, 'results.csv')
                app.write_csv(path)
                with open(path, encoding='utf-8-sig') as f:
                    self.assertIn('1.1.1.1', f.read())
        finally: root.destroy()
