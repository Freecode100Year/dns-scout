"""Windows-only boundary; pass untrusted values as base64 JSON, never shell code."""
import base64
import ipaddress
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

def powershell(script):
    if sys.platform != 'win32': raise OSError('网卡配置仅支持 Windows')
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    run = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], capture_output=True, timeout=180, creationflags=0x08000000)
    if run.returncode: raise RuntimeError(run.stderr.decode('utf-8', errors='replace'))
    return run.stdout.decode('utf-8-sig').strip()

def adapters():
    value = powershell("[Console]::OutputEncoding=[Text.Encoding]::UTF8; @(Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object ifIndex,Name,InterfaceGuid) | ConvertTo-Json -Compress")
    data = json.loads(value or '[]')
    return data if isinstance(data, list) else [data]

def validate_request(action, index, ips):
    if action not in ('apply', 'restore'): raise ValueError('无效操作')
    index = int(index)
    if index < 1: raise ValueError('无效网卡')
    parsed = [str(ipaddress.ip_address(ip)) for ip in ips]
    if action == 'apply' and (not 1 <= len(parsed) <= 2 or len({ipaddress.ip_address(ip).version for ip in parsed}) != 1):
        raise ValueError('请选择 1–2 个同为 IPv4 或同为 IPv6 的 DNS')
    if any(not ipaddress.ip_address(ip).is_global for ip in parsed): raise ValueError('请选择公网 DNS 地址')
    return {'action': action, 'index': index, 'ips': parsed}

def configure(action, index, ips, guid):
    payload = validate_request(action, index, ips)
    payload['guid'] = str(uuid.UUID(guid.strip('{}')))
    with tempfile.TemporaryDirectory(prefix='dns-scout-') as temp:
        status = str(Path(temp) / 'status.json')
        payload['status'] = status
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        script = Path(__file__).with_name('configure.ps1').read_text(encoding='utf-8')
        inner = "$payload='" + data + "';\n" + script
        encoded = base64.b64encode(inner.encode('utf-16le')).decode()
        powershell("$p=Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand','" + encoded + "'); if($p.ExitCode -ne 0){throw '配置失败或 UAC 已取消'}")
        result = json.loads(Path(status).read_text(encoding='utf-8-sig'))
        if not result['ok']: raise RuntimeError(result['message'])
        return result['message']
