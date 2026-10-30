"""Small runtime localization catalog for the desktop UI."""

import json
import locale
import os
from pathlib import Path

SUPPORTED_LANGUAGES = {
    'zh-CN': '简体中文',
    'en': 'English',
}

REGIONS = {
    'global': {'source_key': '全球', 'zh-CN': '全球', 'en': 'Global'},
    'fastest': {'source_key': '网站最快列表', 'zh-CN': '网站最快列表', 'en': 'Website fastest'},
    'china': {'source_key': '中国', 'zh-CN': '中国', 'en': 'China'},
    'hongkong': {'source_key': '香港', 'zh-CN': '香港', 'en': 'Hong Kong'},
    'taiwan': {'source_key': '台湾', 'zh-CN': '台湾', 'en': 'Taiwan'},
    'japan': {'source_key': '日本', 'zh-CN': '日本', 'en': 'Japan'},
    'singapore': {'source_key': '新加坡', 'zh-CN': '新加坡', 'en': 'Singapore'},
    'unitedstates': {'source_key': '美国', 'zh-CN': '美国', 'en': 'United States'},
    'germany': {'source_key': '德国', 'zh-CN': '德国', 'en': 'Germany'},
}

MESSAGES = {
    'zh-CN': {
        'app_title': 'DNS Scout · DNS 优选',
        'subtitle': '从你的网络出发，找到响应更快、更稳定的 DNS。',
        'language': '语言',
        'region': '候选地区',
        'fetch': '获取列表',
        'add_ip': '添加 IP',
        'protocol': '协议',
        'ipv4': 'IPv4',
        'ipv6': 'IPv6',
        'all': '全部',
        'rounds': '轮数',
        'start': '开始优选',
        'stop': '停止',
        'test_domains': '测试域名（逗号分隔）',
        'initial_status': '先获取地区候选列表，或添加自定义公网 DNS。测速不会修改系统配置。',
        'column_ip': 'DNS 地址',
        'column_country': '地区',
        'column_provider': '运营商 / ASN',
        'column_rate': '成功率',
        'column_latency': '中位延迟',
        'column_jitter': '波动 σ',
        'column_error': '最近错误',
        'ipv4_preferred': 'IPv4 首选 DNS',
        'ipv4_alternate': 'IPv4 备用 DNS',
        'ipv6_preferred': 'IPv6 首选 DNS',
        'ipv6_alternate': 'IPv6 备用 DNS',
        'copy': '复制选中 IP',
        'export': '导出 CSV',
        'adapter': '网卡',
        'refresh': '刷新',
        'fill_dns': '填入选中 DNS',
        'apply_dns': '应用 DNS',
        'restore_dns': '恢复原配置',
        'sort_help': '排序：成功率优先 → 中位延迟 → 波动。选中结果后填入对应协议的首选/备用；可手动修改。备用可留空，整组留空则保持原配置。',
        'source_notice': '数据来源 publicdnsserver.com · 本机 UDP/TCP DNS 查询 · 响应有效不代表无污染或隐私可信',
        'candidates_loaded': '{count} 个候选 · {detail}',
        'candidate_count': '{count} 个候选',
        'fetching': '正在获取 HTTPS 候选列表…',
        'fetch_live': '实时列表 · {url}',
        'fetch_cache': '获取失败，使用 {hours:.1f} 小时前缓存 · {detail}',
        'progress': '已完成 {done} / {total} 个服务器',
        'stopped': '已停止；部分测量不宜与完整测量直接比较。',
        'completed': '优选完成。选择结果可复制、导出或设置 DNS。',
        'add_dialog_title': '添加公网 DNS',
        'add_dialog_prompt': '输入 IPv4 / IPv6 地址，多个地址用逗号或空格分隔：',
        'invalid_address': '无效地址',
        'public_ip_only': '只接受公网 IP',
        'waiting_measurement': '{count} 个候选，等待测速',
        'pending': '待测',
        'invalid_rounds': '轮数必须为 1–5（当前为 {value}）',
        'invalid_domains': '请输入 1–10 个域名',
        'no_candidates': '没有符合协议的候选，请获取列表或添加 IP',
        'test_parameters': '测试参数',
        'copied': '选中 IP 已复制',
        'export_title': '导出',
        'run_measurement_first': '请先执行测速',
        'export_failed': '导出失败',
        'select_dns': '选择 DNS',
        'select_dns_limit': '请选中 DNS，每种协议最多两个',
        'select_adapter': '选择网卡',
        'refresh_select_adapter': '请先刷新并选择要操作的网卡',
        'invalid_operation': '无效操作',
        'invalid_adapter': '无效网卡',
        'dns_count_error': '每种协议请选择 1–2 个 DNS，至少填写一种协议',
        'duplicate_dns': '首选与备用 DNS 不能相同',
        'select_public_dns': '请选择公网 DNS 地址',
        'alternate_requires_preferred': 'IPv{family} 备用 DNS 需要先填写首选 DNS',
        'wrong_platform': '网卡配置仅支持 Windows',
        'confirm_adapter': '确认网卡配置',
        'apply_dns_confirm': '将设置 DNS：\n{lines}\n未填写的协议保持原配置。首次修改前会备份该网卡的原配置。',
        'restore_dns_confirm': '将恢复这张网卡首次修改前的 IPv4 / IPv6 DNS 配置。',
        'admin_prompt': '需要接受 Windows 管理员授权。是否继续？',
        'adapter_line': '网卡：{adapter}',
        'operation_failed': '操作失败',
        'setup_failed': '配置失败或 UAC 已取消',
        'target_adapter_changed': '目标网卡已变化，请刷新后重试',
        'cannot_read_dns_mode': '无法读取网卡原始 DNS 模式，已停止修改',
        'dns_set_verified': 'DNS 已设置并校验。原配置备份：{backup}',
        'no_dns_backup': '这张网卡没有原配置备份',
        'backup_adapter_mismatch': '备份网卡标识不匹配',
        'automatic_dns_restore_failed': '自动 DNS 模式恢复校验失败，备份已保留',
        'static_dns_restore_failed': '静态 DNS 恢复校验失败，备份已保留',
        'dns_restored': '原 DNS 配置已恢复并校验',
        'language_save_failed': '无法保存语言偏好：{detail}',
    },
    'en': {
        'app_title': 'DNS Scout · DNS Optimizer',
        'subtitle': 'Find faster, more reliable DNS servers from your network.',
        'language': 'Language',
        'region': 'Candidate region',
        'fetch': 'Get list',
        'add_ip': 'Add IP',
        'protocol': 'Protocol',
        'ipv4': 'IPv4',
        'ipv6': 'IPv6',
        'all': 'All',
        'rounds': 'Rounds',
        'start': 'Find best DNS',
        'stop': 'Stop',
        'test_domains': 'Test domains (comma-separated)',
        'initial_status': 'Get a regional candidate list or add public DNS addresses. Testing never changes system settings.',
        'column_ip': 'DNS address',
        'column_country': 'Region',
        'column_provider': 'Provider / ASN',
        'column_rate': 'Success rate',
        'column_latency': 'Median latency',
        'column_jitter': 'Jitter σ',
        'column_error': 'Latest error',
        'ipv4_preferred': 'IPv4 preferred DNS',
        'ipv4_alternate': 'IPv4 alternate DNS',
        'ipv6_preferred': 'IPv6 preferred DNS',
        'ipv6_alternate': 'IPv6 alternate DNS',
        'copy': 'Copy selected IPs',
        'export': 'Export CSV',
        'adapter': 'Adapter',
        'refresh': 'Refresh',
        'fill_dns': 'Fill selected DNS',
        'apply_dns': 'Apply DNS',
        'restore_dns': 'Restore previous settings',
        'sort_help': 'Sort order: success rate, median latency, then jitter. Select results to fill preferred/alternate addresses for each protocol; you can edit them. Leave an alternate blank, or leave both fields for a protocol blank to keep its current settings.',
        'source_notice': 'Source: publicdnsserver.com · Local UDP/TCP DNS queries · A valid response does not prove an answer is unfiltered or private',
        'candidates_loaded': '{count} candidates · {detail}',
        'candidate_count': '{count} candidates',
        'fetching': 'Fetching HTTPS candidate list…',
        'fetch_live': 'Live list · {url}',
        'fetch_cache': 'Fetch failed; using a {hours:.1f}-hour-old cache · {detail}',
        'progress': 'Completed {done} of {total} servers',
        'stopped': 'Stopped. Partial measurements should not be compared directly with complete runs.',
        'completed': 'Optimization complete. Select results to copy, export, or set DNS.',
        'add_dialog_title': 'Add public DNS',
        'add_dialog_prompt': 'Enter IPv4 / IPv6 addresses, separated by commas or spaces:',
        'invalid_address': 'Invalid address',
        'public_ip_only': 'Only public IP addresses are accepted',
        'waiting_measurement': '{count} candidates, ready to test',
        'pending': 'Pending',
        'invalid_rounds': 'Rounds must be 1–5 (got {value}).',
        'invalid_domains': 'Enter 1–10 domain names',
        'no_candidates': 'No candidates match this protocol. Get a list or add an IP.',
        'test_parameters': 'Test parameters',
        'copied': 'Selected IPs copied',
        'export_title': 'Export',
        'run_measurement_first': 'Run a test before exporting',
        'export_failed': 'Export failed',
        'select_dns': 'Select DNS',
        'select_dns_limit': 'Select DNS results, up to two per protocol',
        'select_adapter': 'Select adapter',
        'refresh_select_adapter': 'Refresh and select a network adapter first',
        'invalid_operation': 'Invalid operation',
        'invalid_adapter': 'Invalid network adapter',
        'dns_count_error': 'Choose 1–2 DNS addresses per protocol and fill at least one protocol',
        'duplicate_dns': 'Preferred and alternate DNS addresses must be different',
        'select_public_dns': 'Choose public DNS addresses',
        'alternate_requires_preferred': 'Enter the preferred IPv{family} DNS before its alternate',
        'wrong_platform': 'Network adapter configuration is only supported on Windows',
        'confirm_adapter': 'Confirm network settings',
        'apply_dns_confirm': 'The following DNS settings will be applied:\n{lines}\nProtocols left blank will keep their current settings. The original settings will be backed up before the first change.',
        'restore_dns_confirm': 'Restore this adapter’s IPv4 / IPv6 DNS settings from its first-change backup.',
        'admin_prompt': 'Windows administrator authorization is required. Continue?',
        'adapter_line': 'Adapter: {adapter}',
        'operation_failed': 'Operation failed',
        'setup_failed': 'Configuration failed or UAC was cancelled',
        'target_adapter_changed': 'The target adapter changed. Refresh and try again.',
        'cannot_read_dns_mode': 'Could not read the adapter’s original DNS mode; no changes were made.',
        'dns_set_verified': 'DNS settings applied and verified. Original settings backup: {backup}',
        'no_dns_backup': 'No original settings backup exists for this adapter',
        'backup_adapter_mismatch': 'The backup does not match this adapter',
        'automatic_dns_restore_failed': 'Automatic DNS restore verification failed; the backup was kept.',
        'static_dns_restore_failed': 'Static DNS restore verification failed; the backup was kept.',
        'dns_restored': 'Original DNS settings restored and verified',
        'language_save_failed': 'Could not save language preference: {detail}',
    },
}


def _language_code(value):
    if not value:
        return None
    value = str(value).strip().replace('-', '_').lower()
    if value.startswith(('en_', 'english')) or value == 'en':
        return 'en'
    if value.startswith(('zh_', 'chinese')) or value == 'zh':
        return 'zh-CN'
    return None


def detect_system_language():
    """Return the OS UI locale where available, otherwise the process locale."""
    try:
        import ctypes
        language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        windows_locale = getattr(locale, 'windows_locale', {})
        detected = windows_locale.get(language_id)
        if detected:
            return detected
    except (AttributeError, OSError):
        pass
    try:
        return locale.getlocale()[0] or ''
    except (ValueError, TypeError):
        return ''


def resolve_language(saved, system):
    return _language_code(saved) or _language_code(system) or 'zh-CN'


def load_language(path, system_language):
    try:
        settings = json.loads(Path(path).read_text(encoding='utf-8'))
        saved = settings.get('language') if isinstance(settings, dict) else None
    except (OSError, ValueError, TypeError):
        saved = None
    return resolve_language(saved, system_language)


def save_language(path, language):
    normalized = _language_code(language)
    if normalized is None:
        raise ValueError('Unsupported language')
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'language': normalized}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def region_labels(language):
    language = resolve_language(language, None)
    return {region_id: values[language] for region_id, values in REGIONS.items()}


def format_message(language, key, **values):
    language = resolve_language(language, None)
    return MESSAGES[language][key].format(**values)


def settings_path():
    root = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'DNSScout'
    return root / 'settings.json'
