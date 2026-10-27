import sys

if __name__ == '__main__':
    if '--smoke-test' in sys.argv:
        import tkinter as tk
        from scout.app import App
        from scout.source import Server
        from scout.benchmark import Result
        root = tk.Tk()
        app = App(root)
        app.servers = [Server('1.1.1.1', 'Australia', 'Cloudflare')]
        app.results = [Result('1.1.1.1', [10,20,30], 3)]
        app.render()
        root.update()
        assert len(app.table.get_children()) == 1
        root.destroy()
    else:
        from scout.app import main
        main()
