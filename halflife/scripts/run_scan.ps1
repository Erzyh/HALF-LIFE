$py = "C:\Users\yeonh\AppData\Local\Programs\Python\Python313\python.exe"
$root = "C:\Users\yeonh\Desktop\NMI_RS\halflife"
$log = "$root\data\scan.log"

while ($true) {
    "[wrapper] start $(Get-Date -Format o)" | Out-File $log -Append -Encoding utf8
    & $py -u "$root\scripts\scan_expand.py" *>> $log
    $code = $LASTEXITCODE
    "[wrapper] exit=$code $(Get-Date -Format o)" | Out-File $log -Append -Encoding utf8
    $done = Select-String -Path $log -Pattern "expanded scan complete" -Quiet
    if ($code -eq 0 -and $done) { break }
    Start-Sleep -Seconds 60
}
"done $(Get-Date -Format o)" | Out-File "$root\data\scan.done" -Encoding ascii
