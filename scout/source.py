"""HTTPS candidate retrieval. Website timing is never local timing."""
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import ipaddress
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

BASE = 'https://publicdnsserver.com/'
PAGES = {'全球': '', '网站最快列表': 'fastest/', '中国': 'china/', '香港': 'hongkong/', '台湾': 'taiwan/', '日本': 'japan/', '新加坡': 'singapore/', '美国': 'unitedstates/', '德国': 'germany/'}

@dataclass
class Server:
    ip: str
    country: str = '自定义'
    provider: str = ''

def parse_servers(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = {}
    for row in soup.select('table tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) < 4: continue
        parts = list(cells[1].stripped_strings)
        if not parts: continue
        try:
            address = ipaddress.ip_address(parts[0])
            if not address.is_global: continue
        except ValueError: continue
        country = cells[2].find('a')
        ip = str(address)
        location = list(cells[2].stripped_strings)
        country_name = country.get_text(strip=True) if country else (location[-1] if location else '未知')
        result[ip] = Server(ip, country_name, ' '.join(parts[1:]))
    if not result: raise ValueError('网站没有返回可识别的 DNS 列表，请稍后重试或添加自定义 IP。')
    return list(result.values())

def fetch_servers(region, cache_dir):
    slug = PAGES[region]
    path = Path(cache_dir) / ('list-' + (slug.strip('/') or 'global') + '.json')
    try:
        request = Request(BASE + slug, headers={'User-Agent': 'DNSScout/1.0 (+https://github.com/Freecode100Year/dns-scout)'})
        with urlopen(request, timeout=20) as response:
            raw = response.read(4_000_001)
        if len(raw) > 4_000_000: raise ValueError('列表响应过大')
        servers = parse_servers(raw.decode('utf-8'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'time': time.time(), 'servers': [asdict(s) for s in servers]}), encoding='utf-8')
        return servers, '实时列表 · ' + BASE + slug
    except Exception as error:
        if not path.exists(): raise
        cached = json.loads(path.read_text(encoding='utf-8'))
        age = max(0, (time.time() - cached['time']) / 3600)
        return [Server(**s) for s in cached['servers']], f'获取失败，使用 {age:.1f} 小时前缓存：{error}'
