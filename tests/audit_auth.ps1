$process = Start-Process python -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000" -PassThru -NoNewWindow
Start-Sleep -Seconds 3

Write-Host "`n--- 1. Health Check ---"
curl http://localhost:8000/api/v1/health

Write-Host "`n--- 2. Login Válido ---"
$loginResp = curl -Method POST "http://localhost:8000/api/v1/auth/login" -Body "username=admin@finanalytics.local&password=admin" -ContentType "application/x-www-form-urlencoded"
$loginResp | ConvertTo-Json -Depth 5

Write-Host "`n--- 3. Login Inválido ---"
try {
    curl -Method POST "http://localhost:8000/api/v1/auth/login" -Body "username=admin@finanalytics.local&password=senha_errada" -ContentType "application/x-www-form-urlencoded"
} catch {
    Write-Host $_.Exception.Message
}

Write-Host "`n--- 4. Seed Automático (verificação banco) ---"
$Result = python -c "import sqlite3; conn=sqlite3.connect('database/fin_analytics.db'); print(conn.execute('select * from users').fetchall())"
if ($Result -like "*admin*") {
    Write-Host "✅ Usuário criado no banco de dados." -ForegroundColor Green
} else {
    Write-Host "❌ Usuário NÃO FOI criado no banco." -ForegroundColor Red
}

Write-Host "Quantidade de usuários cadastrados:"
python -c "import sqlite3; conn=sqlite3.connect('database/fin_analytics.db'); print(conn.execute('select count(*) from users').fetchone())"

Write-Host "`n--- 5. Duplicação de Seed ---"
curl -Method POST "http://localhost:8000/api/v1/auth/login" -Body "username=admin@finanalytics.local&password=admin" -ContentType "application/x-www-form-urlencoded" | Out-Null
curl -Method POST "http://localhost:8000/api/v1/auth/login" -Body "username=admin@finanalytics.local&password=admin" -ContentType "application/x-www-form-urlencoded" | Out-Null
curl -Method POST "http://localhost:8000/api/v1/auth/login" -Body "username=admin@finanalytics.local&password=admin" -ContentType "application/x-www-form-urlencoded" | Out-Null
python -c "import sqlite3; conn=sqlite3.connect('database/fin_analytics.db'); print(conn.execute('select count(*) from users').fetchone())"

Write-Host "`n--- 6. Token JWT ---"
$token = $loginResp.access_token
Write-Host $token

Write-Host "`n--- 7. Endpoint /me ---"
$headers = @{ Authorization="Bearer $token" }
curl "http://localhost:8000/api/v1/auth/me" -Headers $headers | ConvertTo-Json -Depth 5

Write-Host "`n--- 8. Token inválido ---"
$invalidToken = $token.Substring(0, $token.Length - 1) + "a"
$invalidHeaders = @{ Authorization="Bearer $invalidToken" }
try {
    curl "http://localhost:8000/api/v1/auth/me" -Headers $invalidHeaders
} catch {
    Write-Host $_.Exception.Message
}

Write-Host "`nTerminating uvicorn..."
Stop-Process -Id $process.Id -Force
