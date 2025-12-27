Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\\venv")) {
    python -m venv venv
}

.\\venv\\Scripts\\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path ".\\.env")) {
    Copy-Item .\\.env.example .\\.env
}

Write-Host "Setup complete."
Write-Host "Next steps:"
Write-Host "1) alembic upgrade head"
Write-Host "2) uvicorn main:app --reload"
