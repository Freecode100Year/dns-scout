# v0.1.0-preview.1 测试记录

日期：2026-10-27

## 已执行

- Linux Python 3.13 + Xvfb：12 项 unittest 全部通过，包含 Tkinter 界面构建、
  结果显示、选择、CSV 导出、真实本地 UDP DNS 查询、超时失败计数、列表解析、
  成功率排序和系统设置输入校验。
- Windows Python 3.12.10 AMD64，在 Wine 10.0 中运行：相同 12 项测试全部通过。
- PowerShell 7.6.9 Linux：真实 configure.ps1 配合隔离的 Windows API 模拟通过，
  覆盖带花括号 GUID、网卡编号变化、首次静态 DNS 与自动 IPv6 恢复、
  重复设置不覆盖初始备份、未知 GUID 拒绝操作、注册表读取异常阻止修改。
- configure.ps1 通过 PowerShell 语法解析。
- 真实 HTTPS 拉取：中国页 78 个、香港页 76 个、最快页 100 个候选；
  数量是当时页面内容，不是固定收录量。
- Windows Python + PyInstaller 6.19.0 在 Wine 中打包完成，未出现构建警告。
- 生成文件确认为 PE32+ x86-64 Windows GUI 程序。
- 打包后的 DNSScout.exe --smoke-test 成功：启动 Tk 窗口、导入业务模块、
  渲染一行结果、校验界面并正常退出。

## 尚未覆盖

- 真正的 Windows 11 x64 设备上的 UAC 交互、DNS 修改与恢复、VPN/多网卡环境。
- 各地真实网络上的 DNS 性能；此类性能只能在最终用户本机测量。
- 代码签名、SmartScreen 信誉建立。

当前 GitHub OAuth token 不含 workflow 权限，GitHub 拒绝上传工作流；
GitHub 连接器也返回 403。自动构建模板已保存为 docs/windows-build.yml，
并提供 scripts/build-windows.ps1。此次 EXE 属于兼容环境构建的预览版，
不将兼容环境冒烟测试表述为 Windows 11 实机认证。

## 2026-10-28 主备 DNS 扩展验证

- Linux Python 3.13 + Xvfb：16 项 unittest 全部通过。
- 验证四个手动输入框、从选中结果填入、保留未选协议、清空缺失备用、手动主备顺序传递。
- 输入校验覆盖双协议、协议不匹配、仅填写备用、重复 DNS、同协议超量及空配置。
- PowerShell 7 隔离模拟测试通过：同时写入两种协议、各自主备顺序、单协议修改保持另一协议、原配置备份与恢复。
- Windows Python 3.12.10（Wine）下相同 16 项测试全部通过。
- 尚未在真实 Windows 网卡上验收 UAC 和配置变更。

## 2026-10-30 v0.1.0-preview.3 双语界面与发行包

- Wine Windows Python 3.12.10 AMD64：完整 unittest 32/32 通过，包含双语目录、语言保存、UI 即时切换、CSV 标题、地区 slug、DNS 源解析和配置输入校验。
- PowerShell 7.6.9 Linux：`tests/test_configure.ps1` 隔离 API 回归通过；`scout/configure.ps1` 语法解析通过。测试临时目录放在仓库磁盘，避开已满的 `/tmp`；没有修改真实网卡。
- PyInstaller 6.19.0 在 Wine 下构建 `dist/DNSScout.exe`，确认 PE32+ x86-64 Windows GUI，文件大小 12,782,242 bytes。
- `DNSScout.exe --smoke-test` 在 Wine 下退出码 0；校验窗口启动、业务模块导入、结果行渲染和正常退出。
- `dist/SHA256SUMS.txt`：`7efdf5bcf2c17a3c53b92cac8d6181e707b654cd44f6b7b9e5b79754b6b930fb  DNSScout.exe`；`sha256sum -c` 通过。
- `dist/DNSScout-win11-x64.zip` 包含 EXE、README、LICENSE 和 SHA256SUMS。

Wine 构建与冒烟检查不能代替真实 Windows 11 x64 上的 UAC、网卡 DNS 修改/恢复验收。EXE 未签名；SmartScreen 信誉未验证。
