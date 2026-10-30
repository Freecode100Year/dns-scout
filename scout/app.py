import csv
import ipaddress
import math
import os
from pathlib import Path
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from .source import Server, fetch_servers
from .benchmark import measure, rank_key
from . import windows
from .i18n import (
    REGIONS, SUPPORTED_LANGUAGES, detect_system_language, format_message,
    load_language, localize_error, localize_source_text, region_labels, save_language, settings_path,
)

class App:
    def __init__(self, root):
        self.root = root
        self.servers, self.results, self.adapter_map = [], [], {}
        self.preference_path = settings_path()
        self.language = load_language(self.preference_path, detect_system_language())
        self.text_widgets = {}
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.cache = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'DNSScout' / 'cache'
        root.title(self.t('app_title'))
        root.geometry('1120x760')
        root.minsize(960, 660)
        root.configure(bg='#edf2f8')
        self.style = ttk.Style(root)
        style = self.style
        style.theme_use('clam')
        style.configure('.', font=('Microsoft YaHei UI', 10))
        style.configure('TFrame', background='#edf2f8')
        style.configure('TLabel', background='#edf2f8', foreground='#26364c')
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 24, 'bold'), foreground='#14355a')
        style.configure('TButton', padding=(12,8))
        style.configure('Accent.TButton', background='#1665d8', foreground='white')
        style.configure('Treeview', rowheight=30, background='white', fieldbackground='white')
        style.configure('Treeview.Heading', padding=8, font=('Microsoft YaHei UI', 10, 'bold'))
        outer = ttk.Frame(root, padding=24)
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x')
        self.label(header, 'app_name', style='Title.TLabel').pack(side='left')
        self.label(header, 'language').pack(side='right', padx=(8, 4))
        self.language_var = tk.StringVar(value=SUPPORTED_LANGUAGES[self.language])
        self.language_box = ttk.Combobox(header, textvariable=self.language_var, values=list(SUPPORTED_LANGUAGES.values()), state='readonly', width=14)
        self.language_box.pack(side='right')
        self.language_box.bind('<<ComboboxSelected>>', self.on_language_selected)
        self.label(outer, 'subtitle').pack(anchor='w', pady=(4,16))
        row = ttk.Frame(outer)
        row.pack(fill='x')
        self.region_id = 'global'
        self.region_labels = region_labels(self.language)
        self.region = tk.StringVar(value=self.region_labels[self.region_id])
        self.label(row, 'region').pack(side='left')
        self.region_box = ttk.Combobox(row, textvariable=self.region, values=list(self.region_labels.values()), state='readonly', width=16)
        self.region_box.pack(side='left', padx=8)
        self.region_box.bind('<<ComboboxSelected>>', self.on_region_selected)
        self.controls = []
        self.button(row, 'fetch', self.fetch)
        self.button(row, 'add_ip', self.add)
        self.label(row, 'protocol').pack(side='left', padx=(16,4))
        self.family_options = {'ipv4': self.t('ipv4'), 'ipv6': self.t('ipv6'), 'all': self.t('all')}
        self.family_id = 'ipv4'
        self.family = tk.StringVar(value=self.family_options[self.family_id])
        self.family_box = ttk.Combobox(row, textvariable=self.family, values=list(self.family_options.values()), state='readonly', width=9)
        self.family_box.pack(side='left')
        self.family_box.bind('<<ComboboxSelected>>', self.on_family_selected)
        self.rounds = tk.StringVar(value='2')
        self.label(row, 'rounds').pack(side='left', padx=(12,4))
        ttk.Spinbox(row, from_=1, to=5, textvariable=self.rounds, width=3).pack(side='left')
        self.start_button = self.button(row, 'start', self.start, 'Accent.TButton')
        self.stop_button = ttk.Button(row, text=self.t('stop'), command=self.cancel.set, state='disabled')
        self.text_widgets['stop'] = self.stop_button
        self.stop_button.pack(side='left', padx=4)
        config = ttk.Frame(outer)
        config.pack(fill='x', pady=(10,4))
        self.label(config, 'test_domains').pack(side='left')
        self.domains = tk.StringVar(value='example.com,www.microsoft.com,www.baidu.com')
        ttk.Entry(config, textvariable=self.domains).pack(side='left', fill='x', expand=True, padx=8)
        self.status_state = ('initial_status', {})
        self.status = tk.StringVar(value=self.t('initial_status'))
        ttk.Label(outer, textvariable=self.status, wraplength=1020).pack(anchor='w', pady=10)
        self.progress = ttk.Progressbar(outer, mode='determinate')
        self.progress.pack(fill='x', pady=(0,10))
        table_frame = ttk.Frame(outer)
        table_frame.pack(fill='both', expand=True)
        columns = ('ip','country','provider','rate','latency','jitter','error')
        self.column_keys = dict(zip(columns, ('column_ip','column_country','column_provider','column_rate','column_latency','column_jitter','column_error')))
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='extended')
        for name, width in zip(columns, [170,100,215,90,95,85,170]):
            self.table.heading(name, text=self.t(self.column_keys[name]))
            self.table.column(name, width=width, minwidth=65)
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.dns_fields = [tk.StringVar() for _ in range(4)]
        self.dns_label_keys = ('ipv4_preferred','ipv4_alternate','ipv6_preferred','ipv6_alternate')
        self.dns_labels = []
        dns_frame = ttk.Frame(outer)
        dns_frame.pack(fill='x', pady=(10, 0))
        for row_index in range(2):
            for column in range(2):
                key = self.dns_label_keys[row_index * 2 + column]
                label = ttk.Label(dns_frame, text=self.t(key))
                label.grid(row=row_index, column=column * 2, padx=(0, 8), pady=3)
                self.dns_labels.append((key, label))
                entry = ttk.Entry(dns_frame, textvariable=self.dns_fields[row_index * 2 + column], width=30)
                entry.grid(row=row_index, column=column * 2 + 1, sticky='ew', padx=(0, 16), pady=3)
                self.controls.append(entry)
        dns_frame.columnconfigure(1, weight=1)
        dns_frame.columnconfigure(3, weight=1)
        action = ttk.Frame(outer)
        action.pack(fill='x', pady=12)
        self.button(action, 'copy', self.copy)
        self.button(action, 'export', self.export)
        self.label(action, 'adapter').pack(side='left', padx=(12,4))
        self.adapter = tk.StringVar()
        self.adapter_box = ttk.Combobox(action, textvariable=self.adapter, state='readonly', width=18)
        self.adapter_box.pack(side='left')
        self.button(action, 'refresh', self.load_adapters)
        self.button(action, 'fill_dns', self.fill_dns)
        self.button(action, 'apply_dns', lambda: self.change('apply'))
        self.button(action, 'restore_dns', lambda: self.change('restore'))
        self.label(outer, 'sort_help', wraplength=1000).pack(anchor='w')
        self.label(outer, 'source_notice', foreground='#64748b').pack(anchor='w', pady=(5,0))
        self.poll_after_id = root.after(100, self.poll)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def t(self, key, **values):
        return format_message(self.language, key, **values)

    def label(self, frame, key, **kwargs):
        widget = ttk.Label(frame, text=self.t(key), **kwargs)
        self.text_widgets[key] = widget
        return widget

    def button(self, frame, key, command, style='TButton'):
        button = ttk.Button(frame, text=self.t(key), command=command, style=style)
        button.pack(side='left', padx=4)
        self.controls.append(button)
        self.text_widgets[key] = button
        return button

    def on_language_selected(self, _event=None):
        language = next((code for code, label in SUPPORTED_LANGUAGES.items() if label == self.language_var.get()), None)
        if language:
            self.set_language(language)

    def on_region_selected(self, _event=None):
        self.region_id = next((key for key, label in self.region_labels.items() if label == self.region.get()), self.region_id)

    def on_family_selected(self, _event=None):
        self.family_id = next((key for key, label in self.family_options.items() if label == self.family.get()), self.family_id)

    def set_language(self, language):
        if language not in SUPPORTED_LANGUAGES:
            return
        current_region = self.region_id
        try:
            save_language(self.preference_path, language)
        except OSError as exc:
            messagebox.showerror(self.t('operation_failed'), self.t('language_save_failed', detail=str(exc)))
        self.language = language
        self.root.title(self.t('app_title'))
        self.language_var.set(SUPPORTED_LANGUAGES[language])
        self.region_labels = region_labels(language)
        self.region_box.configure(values=list(self.region_labels.values()))
        self.region.set(self.region_labels.get(current_region, next(iter(self.region_labels.values()))))
        self.region_id = current_region if current_region in self.region_labels else next(iter(self.region_labels))
        self.family_options = {'ipv4': self.t('ipv4'), 'ipv6': self.t('ipv6'), 'all': self.t('all')}
        self.family_box.configure(values=list(self.family_options.values()))
        self.family.set(self.family_options[self.family_id])
        for key, widget in self.text_widgets.items():
            widget.configure(text=self.t(key))
        for key, widget in self.dns_labels:
            widget.configure(text=self.t(key))
        for column, key in self.column_keys.items():
            self.table.heading(column, text=self.t(key))
        status_key, status_values = self.status_state
        if status_key == 'backend':
            self.status.set(localize_error(self.language, status_values['raw']))
        else:
            self.status.set(self.t(status_key, **status_values))
        font = 'Segoe UI' if language == 'en' else 'Microsoft YaHei UI'
        self.style.configure('.', font=(font, 10))
        self.style.configure('Title.TLabel', font=(font, 24, 'bold'), foreground='#14355a')
        self.style.configure('Treeview.Heading', padding=8, font=(font, 10, 'bold'))
        self.render()

    def set_status(self, key, **values):
        self.status_state = (key, values)
        self.status.set(self.t(key, **values))

    def set_backend_status(self, raw):
        self.status_state = ('backend', {'raw': str(raw)})
        self.status.set(localize_error(self.language, raw))

    def set_busy(self, value):
        self.busy = value
        for button in self.controls: button.configure(state='disabled' if value else 'normal')
        self.stop_button.configure(state='normal' if value else 'disabled')

    def background(self, job):
        if self.busy: return
        self.cancel.clear()
        self.set_busy(True)
        def run():
            try: job()
            except Exception as exc: self.events.put(('error', str(exc)))
            finally: self.events.put(('done', None))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'servers':
                    self.servers, summary = data
                    self.results = []
                    self.render()
                    detail = self.t('fetch_live', url=summary.url) if summary.mode == 'live' else self.t('fetch_cache', hours=summary.age_hours, detail=localize_error(self.language, summary.error))
                    self.set_status('candidates_loaded', count=len(self.servers), detail=detail)
                elif kind == 'result':
                    self.results.append(data)
                    self.progress['value'] = len(self.results)
                    self.set_status('progress', done=len(self.results), total=int(self.progress['maximum']))
                    self.render()
                elif kind == 'status':
                    if isinstance(data, tuple) and data[0] == 'backend':
                        self.set_backend_status(data[1])
                    else:
                        self.set_status(data)
                elif kind == 'adapters':
                    self.adapter_map = {f'{a["Name"]} (#{a["ifIndex"]})': a for a in data}
                    self.adapter_box['values'] = list(self.adapter_map)
                    self.adapter.set(next(iter(self.adapter_map), ''))
                elif kind == 'error':
                    detail = localize_error(self.language, data)
                    self.set_backend_status(data)
                    messagebox.showerror(self.t('operation_failed'), detail)
                elif kind == 'done': self.set_busy(False)
        except queue.Empty: pass
        self.poll_after_id = self.root.after(100, self.poll)

    def fetch(self):
        self.on_region_selected()
        source_region = REGIONS[self.region_id]['source_key']
        self.set_status('fetching')
        self.background(lambda: self.events.put(('servers', fetch_servers(source_region, self.cache))))

    def add(self):
        text = simpledialog.askstring(self.t('add_dialog_title'), self.t('add_dialog_prompt'))
        if not text: return
        try:
            values = [str(ipaddress.ip_address(x)) for x in text.replace(',', ' ').split()]
            if any(not ipaddress.ip_address(x).is_global for x in values): raise ValueError(self.t('public_ip_only'))
            known = {s.ip for s in self.servers}
            self.servers.extend(Server(ip) for ip in dict.fromkeys(values) if ip not in known)
            self.render()
            self.set_status('waiting_measurement', count=len(self.servers))
        except ValueError as exc: messagebox.showerror(self.t('invalid_address'), localize_error(self.language, exc))

    def start(self):
        try:
            rounds = int(self.rounds.get())
            if not 1 <= rounds <= 5: raise ValueError(self.t('invalid_rounds', value=rounds))
            domains = [x.strip() for x in self.domains.get().replace('，', ',').split(',') if x.strip()]
            import dns.name
            if not 1 <= len(domains) <= 10: raise ValueError(self.t('invalid_domains'))
            for domain in domains: dns.name.from_text(domain).to_wire()
            self.on_family_selected()
            candidates = [s for s in self.servers if self.family_id == 'all' or ipaddress.ip_address(s.ip).version == (4 if self.family_id == 'ipv4' else 6)]
            if not candidates: raise ValueError(self.t('no_candidates'))
        except Exception as exc:
            messagebox.showerror(self.t('test_parameters'), localize_error(self.language, exc))
            return
        self.results = []
        self.render()
        self.progress.configure(maximum=len(candidates), value=0)
        def job():
            with ThreadPoolExecutor(max_workers=16) as pool:
                futures = [pool.submit(measure, s.ip, domains, rounds, 1.5, self.cancel) for s in candidates]
                for future in as_completed(futures):
                    result = future.result()
                    if result.attempts: self.events.put(('result', result))
            self.events.put(('status', 'stopped' if self.cancel.is_set() else 'completed'))
        self.background(job)

    def render(self):
        selected = self.table.selection()
        self.table.delete(*self.table.get_children())
        by_ip = {s.ip: s for s in self.servers}
        measured = {r.ip for r in self.results}
        def fmt(value): return f'{value:.1f} ms' if math.isfinite(value) else '—'
        for r in sorted(self.results, key=rank_key):
            s = by_ip.get(r.ip, Server(r.ip))
            self.table.insert('', 'end', iid=r.ip, values=(r.ip,localize_source_text(self.language, s.country),s.provider,f'{r.successes}/{r.attempts} ({r.ratio:.0%})',fmt(r.median_ms),fmt(r.jitter_ms),localize_error(self.language, r.error)))
        for s in self.servers:
            if s.ip not in measured: self.table.insert('', 'end', iid=s.ip, values=(s.ip,localize_source_text(self.language, s.country),s.provider,self.t('pending'),'—','—',''))
        for ip in selected:
            if self.table.exists(ip): self.table.selection_add(ip)

    def selected_ips(self):
        chosen = set(self.table.selection())
        return [ip for ip in self.table.get_children() if ip in chosen]

    def copy(self):
        ips = self.selected_ips()
        if ips:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(ips))
            self.set_status('copied')

    def write_csv(self, path):
        by_ip = {s.ip: s for s in self.servers}
        with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.writer(handle)
            writer.writerow([self.t(key) for key in ('csv_ip','csv_region','csv_provider','csv_successes','csv_attempts','csv_rate','csv_median','csv_jitter','csv_error')])
            for r in sorted(self.results, key=rank_key):
                s = by_ip.get(r.ip, Server(r.ip))
                # Prevent spreadsheet formulas from remote metadata.
                safe = lambda value: "'" + value if value.startswith(('=','+','-','@')) else value
                writer.writerow([r.ip,safe(s.country),safe(s.provider),r.successes,r.attempts,r.ratio,r.median_ms if r.samples else '',r.jitter_ms if r.samples else '',safe(localize_error(self.language, r.error))])

    def export(self):
        if not self.results:
            messagebox.showinfo(self.t('export_title'), self.t('run_measurement_first'))
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='dns-scout-results.csv', filetypes=[('CSV','*.csv')])
        if path:
            try: self.write_csv(path)
            except OSError as exc: messagebox.showerror(self.t('export_failed'), str(exc))

    def load_adapters(self):
        self.background(lambda: self.events.put(('adapters', windows.adapters())))

    def fill_dns(self):
        groups = {4: [], 6: []}
        for ip in self.selected_ips():
            groups[ipaddress.ip_address(ip).version].append(ip)
        if not any(groups.values()) or any(len(values) > 2 for values in groups.values()):
            messagebox.showerror(self.t('select_dns'), self.t('select_dns_limit'))
            return
        for family, offset in ((4, 0), (6, 2)):
            if groups[family]:
                for position in range(2):
                    self.dns_fields[offset + position].set(groups[family][position] if position < len(groups[family]) else '')

    def change(self, action):
        adapter = self.adapter_map.get(self.adapter.get())
        if not adapter:
            messagebox.showinfo(self.t('select_adapter'), self.t('refresh_select_adapter'))
            return
        index = adapter['ifIndex']
        try:
            ips = windows.dns_slots(*(field.get() for field in self.dns_fields)) if action == 'apply' else []
            windows.validate_request(action, index, ips)
        except ValueError as exc:
            messagebox.showerror(self.t('select_dns'), localize_error(self.language, exc))
            return
        lines = '\n'.join(
            f"IPv{family} {self.t(role)}: {ip}"
            for family in (4, 6)
            for role, ip in zip(
                ('preferred', 'alternate'),
                [address for address in ips if ipaddress.ip_address(address).version == family],
            )
        )
        text = self.t('apply_dns_confirm', lines=lines) if action == 'apply' else self.t('restore_dns_confirm')
        confirm = f"{self.t('adapter_line', adapter=self.adapter.get())}\n{text}\n{self.t('admin_prompt')}"
        if not messagebox.askyesno(self.t('confirm_adapter'), confirm): return
        self.background(lambda: self.events.put(('status', ('backend', windows.configure(action, index, ips, adapter['InterfaceGuid'])))))

    def close(self):
        self.cancel.set()
        if self.poll_after_id is not None:
            try:
                self.root.after_cancel(self.poll_after_id)
            except tk.TclError:
                pass
            self.poll_after_id = None
        self.root.destroy()

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
