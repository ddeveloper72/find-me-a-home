# Initialize Git Repository Script
# Run this once to set up version control

Write-Host "Initializing Git repository for Find Me a Home..." -ForegroundColor Green
Write-Host ""

# Initialize git if not already done
if (-not (Test-Path ".git")) {
    git init
    Write-Host "✓ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✓ Git repository already exists" -ForegroundColor Yellow
}

# Create .env file from example if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file from .env.example" -ForegroundColor Green
    Write-Host "  Please edit .env with your configuration" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Yellow
}

# Stage all files
Write-Host ""
Write-Host "Staging files for initial commit..." -ForegroundColor Green
git add .

# Show status
Write-Host ""
Write-Host "Git status:" -ForegroundColor Green
git status

# Make initial commit
Write-Host ""
$commit = Read-Host "Make initial commit? (y/n)"
if ($commit -eq "y") {
    git commit -m "Initial commit: Find Me a Home application structure"
    Write-Host "✓ Initial commit created" -ForegroundColor Green
    
    # Ask about remote repository
    Write-Host ""
    $addRemote = Read-Host "Add remote repository? (y/n)"
    if ($addRemote -eq "y") {
        $remoteUrl = Read-Host "Enter remote repository URL (e.g., https://github.com/username/repo.git)"
        git remote add origin $remoteUrl
        Write-Host "✓ Remote repository added" -ForegroundColor Green
        Write-Host "  You can now push with: git push -u origin main" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Git setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env with your configuration" -ForegroundColor White
Write-Host "2. Set up virtual environment: python -m venv .venv" -ForegroundColor White
Write-Host "3. Activate virtual environment: .\.venv\Scripts\activate" -ForegroundColor White
Write-Host "4. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "5. See QUICKSTART.md for full setup instructions" -ForegroundColor White
Write-Host ""
