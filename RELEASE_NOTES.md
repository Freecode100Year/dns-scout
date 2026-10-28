DNS Scout v0.1.0 Preview 2 · Windows x64 便携版

- 新增 IPv4 和 IPv6 各自的首选 DNS、备用 DNS 输入框，支持手动填写和从测速结果填入。
- 一次应用两种协议，分别校验主备顺序；未填写的协议保持原配置。
- 校验仅填写备用、重复 DNS、地址协议不匹配等输入，保留首次备份与恢复功能。

下载 DNSScout.exe 即可运行，无需安装 Python；SHA256SUMS.txt 可核对完整性。

验证：Linux 与 Windows Python（Wine）各 16 项测试通过，PowerShell 配置隔离回归通过。
构建日志随发布提供。

本版由 Windows Python 3.12 + PyInstaller 在 Wine 中构建；真正 Windows 11 上的
UAC/网卡修改恢复尚待实机验收。程序未签名。
