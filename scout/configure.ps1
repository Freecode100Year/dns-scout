$ErrorActionPreference = 'Stop'
$p = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload)) | ConvertFrom-Json
try {
    $guid = ([guid]$p.guid).ToString('D')
    $matchesByGuid = @(Get-NetAdapter | Where-Object { ([guid]$_.InterfaceGuid).ToString('D') -eq $guid })
    if ($matchesByGuid.Count -ne 1) {throw '目标网卡已变化，请刷新后重试'}
    $adapter = $matchesByGuid[0]
    $p.index = $adapter.ifIndex
    $folder = Join-Path $env:LOCALAPPDATA 'DNSScout\backups'
    New-Item -ItemType Directory -Force $folder | Out-Null
    $backup = Join-Path $folder ($guid + '.json')
    function Read-State {
        $states = @()
        foreach ($family in @('IPv4','IPv6')) {
            $service = if ($family -eq 'IPv4') {'Tcpip'} else {'Tcpip6'}
            $key = "HKLM:\SYSTEM\CurrentControlSet\Services\$service\Parameters\Interfaces\{$guid}"
            if (-not (Test-Path -Path $key -ErrorAction Stop)) {throw '无法读取网卡原始 DNS 模式，已停止修改'}
            $properties = Get-ItemProperty -Path $key -ErrorAction Stop
            $static = $properties.NameServer
            $addresses = @((Get-DnsClientServerAddress -InterfaceIndex $p.index -AddressFamily $family).ServerAddresses)
            $states += @{family=$family; automatic=[string]::IsNullOrWhiteSpace($static); addresses=$addresses}
        }
        return $states
    }
    if ($p.action -eq 'apply') {
        if (-not (Test-Path $backup)) {
            @{guid=$guid; name=$adapter.Name; states=@(Read-State)} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $backup
        }
        foreach ($family in @('IPv4','IPv6')) {
            $requested = @($p.ips | Where-Object { ($_.Contains(':')) -eq ($family -eq 'IPv6') })
            if ($requested.Count -eq 0) {continue}
            $target = Get-DnsClientServerAddress -InterfaceIndex $p.index -AddressFamily $family
            $target | Set-DnsClientServerAddress -ServerAddresses $requested
            $actual = @((Get-DnsClientServerAddress -InterfaceIndex $p.index -AddressFamily $family).ServerAddresses)
            if (($actual -join ',') -ne ($requested -join ',')) {throw "$family 写入后校验失败，原配置备份已保留，请恢复"}
        }
        $message = "DNS 已设置并校验。原配置备份：$backup"
    } else {
        if (-not (Test-Path $backup)) {throw '这张网卡没有原配置备份'}
        $saved = Get-Content -Raw -Encoding UTF8 $backup | ConvertFrom-Json
        if ($saved.guid -ne $guid) {throw '备份网卡标识不匹配'}
        foreach ($state in $saved.states) {
            $target = Get-DnsClientServerAddress -InterfaceIndex $p.index -AddressFamily $state.family
            if ($state.automatic) {$target | Set-DnsClientServerAddress -ResetServerAddresses}
            else {$target | Set-DnsClientServerAddress -ServerAddresses @($state.addresses)}
        }
        $current = @(Read-State)
        foreach ($state in $saved.states) {
            $now = $current | Where-Object family -eq $state.family
            if ($now.automatic -ne $state.automatic) {throw '自动 DNS 模式恢复校验失败，备份已保留'}
            if (-not $state.automatic -and (($now.addresses -join ',') -ne ($state.addresses -join ','))) {throw '静态 DNS 恢复校验失败，备份已保留'}
        }
        Remove-Item $backup
        $message = '原 DNS 配置已恢复并校验'
    }
    @{ok=$true; message=$message} | ConvertTo-Json | Set-Content -Encoding UTF8 $p.status
} catch {
    @{ok=$false; message=$_.Exception.Message} | ConvertTo-Json | Set-Content -Encoding UTF8 $p.status
}
