param (
    [string]$EnvFile = ".env"
)

Write-Host "--- 1. Carregando variáveis do arquivo $EnvFile ---"
if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match "^#" -or [string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $key, $value = $line -split '=', 2
        $key = $key.Trim()
        $value = $value.Trim()
        
        # Remove aspas se houver
        if ($value -match "^`"(.*)`"$") {
            $value = $matches[1]
        } elseif ($value -match "^'(.*)'$") {
            $value = $matches[1]
        }
        
        # Define variável de ambiente
        [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
        # Write-Host "Exportado: $key"
    }
} else {
    Write-Host "[ERROR] Arquivo $EnvFile não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "--- 2. Validando Exportação ---"
Write-Host "PIERRE_API_KEY = $($env:PIERRE_API_KEY)"

Write-Host "--- 3. Iniciando MCP via Node/npx ---"
if ([string]::IsNullOrEmpty($env:PIERRE_API_KEY)) {
    Write-Host "[WARNING] PIERRE_API_KEY está vazia. O MCP pode falhar na autenticação." -ForegroundColor Yellow
}

# Iniciando o MCP
npx -y mcp-remote https://pierre.finance/mcp --header "Authorization:Bearer $($env:PIERRE_API_KEY)"
