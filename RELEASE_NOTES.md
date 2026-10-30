# DNS Scout v0.1.0-preview.3 · Windows x64 portable

## 简体中文

- 新增简体中文 / English 双语界面，可随时切换并保存选择；首次启动跟随 Windows 显示语言。
- 地区、状态、校验提示、网卡确认框、表格与 CSV 标题随界面语言切换。
- 保持当前测速结果、输入内容和地区选择；保留原有 DNS 测量与系统配置行为。
- 关闭窗口时取消待处理的 UI 定时回调，避免关闭过程产生 Tcl 错误。

下载 `DNSScout.exe` 即可运行，无需安装 Python；使用 `SHA256SUMS.txt` 核对文件。

## English

- Added Simplified Chinese and English UI, with live switching and a saved language preference. The first launch follows the Windows display language.
- Region names, status messages, validation prompts, adapter confirmations, table headings, and CSV headers follow the selected language.
- Switching languages preserves current results, inputs, and region selection. DNS measurement and system configuration behavior remain unchanged.
- Closing the window now cancels its pending UI timer callback.

Download `DNSScout.exe` and run it without installing Python. Verify the file with `SHA256SUMS.txt`.

## Verification / 验证

- Python unit, UI, localization, and source-fetch tests run under Windows Python 3.12 in Wine.
- PowerShell configuration tests run with isolated Windows API mocks; no real network adapter is modified by the test suite.
- The release executable is built with PyInstaller 6.19.0 under Wine and smoke-tested with `--smoke-test`.
- This compatibility environment does not replace Windows 11 real-device testing of UAC and DNS adapter changes. The executable is unsigned.
