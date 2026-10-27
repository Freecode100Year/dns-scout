DNS Scout 首个中文 Windows 11 x64 便携预览版，无需安装 Python。

功能：
- publicdnsserver.com 地区候选列表、离线缓存、自定义 IPv4/IPv6。
- 本机 DNS 查询，按成功率、中位延迟与波动排序；停止、复制、CSV。
- 指定网卡后通过 UAC 设置 DNS，保存原配置，支持静态/自动模式恢复与校验。

下载 DNSScout.exe 即可运行，或下载 ZIP；SHA256SUMS.txt 可核对完整性。

验证：Linux 和 Windows Python（Wine）各 12 项测试通过，PowerShell 配置隔离回归通过，
EXE 打包及打包后界面启动冒烟测试通过。BUILD_LOG.txt 提供构建记录。

限制：本版由 Windows Python 在 Wine 中构建；真正 Windows 11 上的 UAC/网卡修改恢复
尚待实机验收。程序未签名。GitHub 自动构建仍需 workflow 授权。
完整测试记录见仓库 docs/TESTING.md。
