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
from .source import Server, PAGES, fetch_servers
from .benchmark import measure, rank_key
from . import windows

class App:
    def __init__(self, root):
        self.root = root
        self.servers, self.results, self.adapter_map = [], [], {}
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.cache = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'DNSScout' / 'cache'
        root.title('DNS Scout · DNS 优选')
        root.geometry('1120x760')
        root.minsize(960, 660)
        root.configure(bg='#edf2f8')
        style = ttk.Style(root)
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
        ttk.Label(outer, text='DNS Scout', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='从你的网络出发，找到响应更快、更稳定的 DNS。').pack(anchor='w', pady=(4,16))
        row = ttk.Frame(outer)
        row.pack(fill='x')
        self.region = tk.StringVar(value='中国')
        ttk.Label(row, text='候选地区').pack(side='left')
        ttk.Combobox(row, textvariable=self.region, values=list(PAGES), state='readonly', width=14).pack(side='left', padx=8)
        self.controls = []
        self.button(row, '获取列表', self.fetch)
        self.button(row, '添加 IP', self.add)
        ttk.Label(row, text='协议').pack(side='left', padx=(16,4))
        self.family = tk.StringVar(value='IPv4')
        ttk.Combobox(row, textvariable=self.family, values=['IPv4','IPv6','全部'], state='readonly', width=7).pack(side='left')
        self.rounds = tk.StringVar(value='2')
        ttk.Label(row, text='轮数').pack(side='left', padx=(12,4))
        ttk.Spinbox(row, from_=1, to=5, textvariable=self.rounds, width=3).pack(side='left')
        self.button(row, '开始优选', self.start, 'Accent.TButton')
        self.stop_button = ttk.Button(row, text='停止', command=self.cancel.set, state='disabled')
        self.stop_button.pack(side='left', padx=4)
        config = ttk.Frame(outer)
        config.pack(fill='x', pady=(10,4))
        ttk.Label(config, text='测试域名（逗号分隔）').pack(side='left')
        self.domains = tk.StringVar(value='example.com,www.microsoft.com,www.baidu.com')
        ttk.Entry(config, textvariable=self.domains).pack(side='left', fill='x', expand=True, padx=8)
        self.status = tk.StringVar(value='先获取地区候选列表，或添加自定义公网 DNS。测速不会修改系统配置。')
        ttk.Label(outer, textvariable=self.status, wraplength=1020).pack(anchor='w', pady=10)
        self.progress = ttk.Progressbar(outer, mode='determinate')
        self.progress.pack(fill='x', pady=(0,10))
        table_frame = ttk.Frame(outer)
        table_frame.pack(fill='both', expand=True)
        columns = ('ip','country','provider','rate','latency','jitter','error')
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='extended')
        for name, text, width in zip(columns, ['DNS 地址','地区','运营商 / ASN','成功率','中位延迟','波动 σ','最近错误'], [170,100,215,90,95,85,170]):
            self.table.heading(name, text=text)
            self.table.column(name, width=width, minwidth=65)
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.dns_fields = [tk.StringVar() for _ in range(4)]
        dns_frame = ttk.Frame(outer)
        dns_frame.pack(fill='x', pady=(10, 0))
        for row_index, family in enumerate(('IPv4', 'IPv6')):
            for column, role in enumerate(('首选 DNS', '备用 DNS')):
                ttk.Label(dns_frame, text=f'{family} {role}').grid(row=row_index, column=column * 2, padx=(0, 8), pady=3)
                entry = ttk.Entry(dns_frame, textvariable=self.dns_fields[row_index * 2 + column], width=30)
                entry.grid(row=row_index, column=column * 2 + 1, sticky='ew', padx=(0, 16), pady=3)
                self.controls.append(entry)
        dns_frame.columnconfigure(1, weight=1)
        dns_frame.columnconfigure(3, weight=1)
        action = ttk.Frame(outer)
        action.pack(fill='x', pady=12)
        self.button(action, '复制选中 IP', self.copy)
        self.button(action, '导出 CSV', self.export)
        ttk.Label(action, text='网卡').pack(side='left', padx=(12,4))
        self.adapter = tk.StringVar()
        self.adapter_box = ttk.Combobox(action, textvariable=self.adapter, state='readonly', width=18)
        self.adapter_box.pack(side='left')
        self.button(action, '刷新', self.load_adapters)
        self.button(action, '填入选中 DNS', self.fill_dns)
        self.button(action, '应用 DNS', lambda: self.change('apply'))
        self.button(action, '恢复原配置', lambda: self.change('restore'))
        ttk.Label(outer, text='排序：成功率优先 → 中位延迟 → 波动。选中结果后填入对应协议的首选/备用；可手动修改。备用可留空，整组留空则保持原配置。', wraplength=1000).pack(anchor='w')
        ttk.Label(outer, text='数据来源 publicdnsserver.com · 本机 UDP/TCP DNS 查询 · 响应有效不代表无污染或隐私可信', foreground='#64748b').pack(anchor='w', pady=(5,0))
        root.after(100, self.poll)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def button(self, frame, text, command, style='TButton'):
        button = ttk.Button(frame, text=text, command=command, style=style)
        button.pack(side='left', padx=4)
        self.controls.append(button)
        return button

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
                    self.servers, description = data
                    self.results = []
                    self.render()
                    self.status.set(f'{len(self.servers)} 个候选 · {description}')
                elif kind == 'result':
                    self.results.append(data)
                    self.progress['value'] = len(self.results)
                    self.status.set(f'已完成 {len(self.results)} / {int(self.progress["maximum"])} 个服务器')
                    self.render()
                elif kind == 'status': self.status.set(data)
                elif kind == 'adapters':
                    self.adapter_map = {f'{a["Name"]} (#{a["ifIndex"]})': a for a in data}
                    self.adapter_box['values'] = list(self.adapter_map)
                    self.adapter.set(next(iter(self.adapter_map), ''))
                elif kind == 'error':
                    self.status.set(data)
                    messagebox.showerror('操作失败', data)
                elif kind == 'done': self.set_busy(False)
        except queue.Empty: pass
        self.root.after(100, self.poll)

    def fetch(self):
        region = self.region.get()
        self.status.set('正在获取 HTTPS 候选列表…')
        self.background(lambda: self.events.put(('servers', fetch_servers(region, self.cache))))

    def add(self):
        text = simpledialog.askstring('添加公网 DNS', '输入 IPv4 / IPv6 地址，多个地址用逗号或空格分隔：')
        if not text: return
        try:
            values = [str(ipaddress.ip_address(x)) for x in text.replace(',', ' ').split()]
            if any(not ipaddress.ip_address(x).is_global for x in values): raise ValueError('只接受公网 IP')
            known = {s.ip for s in self.servers}
            self.servers.extend(Server(ip) for ip in dict.fromkeys(values) if ip not in known)
            self.render()
            self.status.set(f'{len(self.servers)} 个候选，等待测速')
        except ValueError as exc: messagebox.showerror('无效地址', str(exc))

    def start(self):
        try:
            rounds = int(self.rounds.get())
            if not 1 <= rounds <= 5: raise ValueError('轮数必须为 1–5')
            domains = [x.strip() for x in self.domains.get().replace('，', ',').split(',') if x.strip()]
            import dns.name
            if not 1 <= len(domains) <= 10: raise ValueError('请输入 1–10 个域名')
            for domain in domains: dns.name.from_text(domain).to_wire()
            family = self.family.get()
            candidates = [s for s in self.servers if family == '全部' or ipaddress.ip_address(s.ip).version == (4 if family == 'IPv4' else 6)]
            if not candidates: raise ValueError('没有符合协议的候选，请获取列表或添加 IP')
        except Exception as exc:
            messagebox.showerror('测试参数', str(exc))
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
            self.events.put(('status', '已停止；部分测量不宜与完整测量直接比较。' if self.cancel.is_set() else '优选完成。选择结果可复制、导出或设置 DNS。'))
        self.background(job)

    def render(self):
        selected = self.table.selection()
        self.table.delete(*self.table.get_children())
        by_ip = {s.ip: s for s in self.servers}
        measured = {r.ip for r in self.results}
        def fmt(value): return f'{value:.1f} ms' if math.isfinite(value) else '—'
        for r in sorted(self.results, key=rank_key):
            s = by_ip.get(r.ip, Server(r.ip))
            self.table.insert('', 'end', iid=r.ip, values=(r.ip,s.country,s.provider,f'{r.successes}/{r.attempts} ({r.ratio:.0%})',fmt(r.median_ms),fmt(r.jitter_ms),r.error))
        for s in self.servers:
            if s.ip not in measured: self.table.insert('', 'end', iid=s.ip, values=(s.ip,s.country,s.provider,'待测','—','—',''))
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
            self.status.set('选中 IP 已复制')

    def write_csv(self, path):
        by_ip = {s.ip: s for s in self.servers}
        with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.writer(handle)
            writer.writerow(['DNS','地区','运营商','成功次数','请求次数','成功率','中位延迟ms','波动ms','最近错误'])
            for r in sorted(self.results, key=rank_key):
                s = by_ip.get(r.ip, Server(r.ip))
                # Prevent spreadsheet formulas from remote metadata.
                safe = lambda value: "'" + value if value.startswith(('=','+','-','@')) else value
                writer.writerow([r.ip,safe(s.country),safe(s.provider),r.successes,r.attempts,r.ratio,r.median_ms if r.samples else '',r.jitter_ms if r.samples else '',safe(r.error)])

    def export(self):
        if not self.results:
            messagebox.showinfo('导出', '请先执行测速')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile='dns-scout-results.csv', filetypes=[('CSV','*.csv')])
        if path:
            try: self.write_csv(path)
            except OSError as exc: messagebox.showerror('导出失败', str(exc))

    def load_adapters(self):
        self.background(lambda: self.events.put(('adapters', windows.adapters())))

    def fill_dns(self):
        groups = {4: [], 6: []}
        for ip in self.selected_ips():
            groups[ipaddress.ip_address(ip).version].append(ip)
        if not any(groups.values()) or any(len(values) > 2 for values in groups.values()):
            messagebox.showerror('选择 DNS', '请选中 DNS，每种协议最多两个')
            return
        for family, offset in ((4, 0), (6, 2)):
            if groups[family]:
                for position in range(2):
                    self.dns_fields[offset + position].set(groups[family][position] if position < len(groups[family]) else '')

    def change(self, action):
        adapter = self.adapter_map.get(self.adapter.get())
        if not adapter:
            messagebox.showinfo('选择网卡', '请先刷新并选择要操作的网卡')
            return
        index = adapter['ifIndex']
        try:
            ips = windows.dns_slots(*(field.get() for field in self.dns_fields)) if action == 'apply' else []
            windows.validate_request(action, index, ips)
        except ValueError as exc:
            messagebox.showerror('选择 DNS', str(exc))
            return
        text = ('将设置 DNS：\n' + '\n'.join(f"IPv{family} {role}：{ip}" for family in (4, 6) for role, ip in zip(('首选', '备用'), [ip for ip in ips if ipaddress.ip_address(ip).version == family])) + '\n未填写的协议保持原配置。首次修改前会备份该网卡的原配置。') if action == 'apply' else '将恢复这张网卡首次修改前的 IPv4 / IPv6 DNS 配置。'
        if not messagebox.askyesno('确认网卡配置', f'网卡：{self.adapter.get()}\n{text}\n需要接受 Windows 管理员授权。是否继续？'): return
        self.background(lambda: self.events.put(('status', windows.configure(action, index, ips, adapter['InterfaceGuid']))))

    def close(self):
        self.cancel.set()
        self.root.destroy()

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
