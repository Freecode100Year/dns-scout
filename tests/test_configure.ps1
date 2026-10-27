# Runs the real configuration script with mocked Windows APIs; never touches a real adapter.
$ErrorActionPreference = 'Stop'
$originalLocalAppData = $env:LOCALAPPDATA
$testFolder = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
$env:LOCALAPPDATA = $testFolder
New-Item -ItemType Directory $testFolder | Out-Null
$script:guid = '01234567-89ab-cdef-0123-456789abcdef'
$script:state = @{
    IPv4 = @{automatic=$false; addresses=@('9.9.9.9','149.112.112.112')}
    IPv6 = @{automatic=$true; addresses=@('2606:4700:4700::1111')}
}
$script:mutations = 0
$script:registryFailure = $false
function Get-NetAdapter {
    param($InterfaceIndex)
    [pscustomobject]@{InterfaceGuid="{$script:guid}"; ifIndex=7; Name='Mock adapter'}
}
function Get-ItemProperty {
    [CmdletBinding()]
    param($Path,$Name)
    if ($script:registryFailure) { throw 'registry denied' }
    if ($Path -notmatch '\\Interfaces\\\{01234567-89ab-cdef-0123-456789abcdef\}$') { return $null }
    $family = if ($Path.Contains('Tcpip6')) {'IPv6'} else {'IPv4'}
    $value = if ($script:state[$family].automatic) {''} else {$script:state[$family].addresses -join ','}
    [pscustomobject]@{NameServer=$value}
}
function Test-Path {
    [CmdletBinding()]
    param([Parameter(Position=0)]$Path)
    if ($Path -like 'HKLM:*') { return $true }
    Microsoft.PowerShell.Management\Test-Path $Path
}
function Get-DnsClientServerAddress {
    param($InterfaceIndex,$AddressFamily)
    if ($InterfaceIndex -ne 7) { throw 'Wrong adapter targeted' }
    [pscustomobject]@{AddressFamily=$AddressFamily; ServerAddresses=@($script:state[$AddressFamily].addresses)}
}
function Set-DnsClientServerAddress {
    param([Parameter(ValueFromPipeline)]$InputObject, $ServerAddresses, [switch]$ResetServerAddresses)
    process {
        $script:mutations++
        $family = $InputObject.AddressFamily
        if ($ResetServerAddresses) {$script:state[$family] = @{automatic=$true; addresses=@()}}
        else {$script:state[$family] = @{automatic=$false; addresses=@($ServerAddresses)}}
    }
}
function Assert($condition, $message) { if (-not $condition) { throw $message } }
function Invoke-Config($action, $ips, $guid=$script:guid) {
    # Stale index deliberately points elsewhere; GUID must resolve the intended adapter to index 7.
    $request = @{action=$action; ips=@($ips); index=99; guid=$guid; status=(Join-Path $testFolder 'status.json')}
    $payload = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($request | ConvertTo-Json -Compress)))
    . (Join-Path $PSScriptRoot '../scout/configure.ps1')
    return Get-Content -Raw $request.status | ConvertFrom-Json
}
try {
    $result = Invoke-Config 'apply' @('1.1.1.1','8.8.8.8')
    Assert $result.ok ("Apply failed: " + $result.message)
    $backupPath = Join-Path $testFolder "DNSScout/backups/$script:guid.json"
    $backup = Get-Content -Raw $backupPath | ConvertFrom-Json
    $v4 = $backup.states | Where-Object family -eq 'IPv4'
    Assert (-not $v4.automatic) 'Static IPv4 was incorrectly backed up as automatic'
    Assert (($v4.addresses -join ',') -eq '9.9.9.9,149.112.112.112') 'Original DNS addresses lost'
    $result = Invoke-Config 'apply' @('8.8.4.4')
    Assert $result.ok 'Repeated apply failed'
    $backup = Get-Content -Raw $backupPath | ConvertFrom-Json
    Assert ((($backup.states | Where-Object family -eq 'IPv4').addresses -join ',') -eq '9.9.9.9,149.112.112.112') 'Repeated apply overwrote initial backup'
    $result = Invoke-Config 'restore' @()
    Assert $result.ok ("Restore failed: " + $result.message)
    Assert (-not $script:state.IPv4.automatic) 'Static mode not restored'
    Assert (($script:state.IPv4.addresses -join ',') -eq '9.9.9.9,149.112.112.112') 'Static addresses not restored'
    Assert $script:state.IPv6.automatic 'Automatic IPv6 mode not restored'
    Assert (-not (Test-Path $backupPath)) 'Verified restored backup not deleted'
    $before = $script:mutations
    $result = Invoke-Config 'apply' @('1.1.1.1') 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
    Assert (-not $result.ok) 'Unknown adapter GUID accepted'
    Assert ($script:mutations -eq $before) 'Unknown GUID mutated adapter'
    $script:registryFailure = $true
    $result = Invoke-Config 'apply' @('1.1.1.1')
    Assert (-not $result.ok) 'Registry failure was silently accepted'
    Assert ($script:mutations -eq $before) 'DNS mutated without readable original state'
    'PASS: braced GUID, stale index, static/automatic restore, repeated apply, unknown GUID and registry failure'
} finally {
    $env:LOCALAPPDATA = $originalLocalAppData
    Remove-Item -Recurse -Force $testFolder
}
