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
