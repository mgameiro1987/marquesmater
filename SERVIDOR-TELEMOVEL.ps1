$ErrorActionPreference='Stop'
$root=(Get-Location).Path
$port=8000
$listener=New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any,$port)
$listener.Start()
Write-Host ''
Write-Host 'MARQUESMATER - SERVIDOR LOCAL' -ForegroundColor Cyan
Write-Host 'PC: http://localhost:8000'
Write-Host 'No telemovel: http://IP-DO-PC:8000' -ForegroundColor Green
Write-Host 'Nao feche esta janela enquanto estiver a testar.' -ForegroundColor Yellow
function Mime($p){switch([IO.Path]::GetExtension($p).ToLower()){'.html'{'text/html; charset=utf-8';break}'.css'{'text/css; charset=utf-8';break}'.js'{'application/javascript; charset=utf-8';break}'.svg'{'image/svg+xml';break}'.png'{'image/png';break}'.jpg'{'image/jpeg';break}'.webp'{'image/webp';break}default{'application/octet-stream'}}}
try{while($true){$c=$listener.AcceptTcpClient();$s=$c.GetStream();$r=New-Object IO.StreamReader($s);$line=$r.ReadLine();while(($h=$r.ReadLine()) -ne ''){};if($line -match '^GET\s+(\S+)'){$u=$matches[1].Split('?')[0];$u=[Uri]::UnescapeDataString($u);if($u -eq '/'){$u='/index.html'};$rel=$u.TrimStart('/').Replace('/',[IO.Path]::DirectorySeparatorChar);$f=[IO.Path]::GetFullPath((Join-Path $root $rel));if(-not $f.StartsWith([IO.Path]::GetFullPath($root),[StringComparison]::OrdinalIgnoreCase)-or -not(Test-Path -LiteralPath $f -PathType Leaf)){$b=[Text.Encoding]::UTF8.GetBytes('<h1>404</h1>');$st='404 Not Found';$m='text/html; charset=utf-8'}else{$b=[IO.File]::ReadAllBytes($f);$st='200 OK';$m=Mime $f};$head=[Text.Encoding]::ASCII.GetBytes("HTTP/1.1 $st`r`nContent-Type: $m`r`nContent-Length: $($b.Length)`r`nConnection: close`r`n`r`n");$s.Write($head,0,$head.Length);$s.Write($b,0,$b.Length);$s.Flush()}}$r.Dispose();$s.Dispose();$c.Close()}}finally{$listener.Stop()}
