$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
python -m pip install -r requirements.txt pyinstaller==6.19.0
if ($LASTEXITCODE) {throw 'Dependency installation failed'}
python -m unittest discover -s tests -v
if ($LASTEXITCODE) {throw 'Python tests failed'}
& ./tests/test_configure.ps1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name DNSScout --add-data 'scout/configure.ps1;scout' main.py
if ($LASTEXITCODE) {throw 'EXE build failed'}
$p = Start-Process ./dist/DNSScout.exe -ArgumentList '--smoke-test' -PassThru
if (-not $p.WaitForExit(60000)) {$p.Kill(); throw 'Smoke test timed out'}
if ($p.ExitCode -ne 0) {throw 'Smoke test failed'}
$hash = (Get-FileHash ./dist/DNSScout.exe -Algorithm SHA256).Hash.ToLower()
"$hash  DNSScout.exe" | Set-Content -Encoding utf8 ./dist/SHA256SUMS.txt
Write-Output 'Build and smoke test passed: dist/DNSScout.exe'
