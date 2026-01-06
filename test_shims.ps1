# Test script to verify kotorcli and kotordiff shims work correctly
# Run from repo root

Write-Host "=== Testing PyKotor CLI Entry Points ===" -ForegroundColor Cyan

# Test pykotor.cli imports
Write-Host "`n1. Testing pykotor.cli imports..." -ForegroundColor Yellow
$env:PYTHONPATH = "Libraries\PyKotor\src"
try {
    python -c "from pykotor.cli.__main__ import main; print('✓ pykotor.cli.__main__.main imported')"
}
catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test pykotor.diff_tool imports
Write-Host "`n2. Testing pykotor.diff_tool imports..." -ForegroundColor Yellow
try {
    python -c "from pykotor.diff_tool.__main__ import main; print('✓ pykotor.diff_tool.__main__.main imported')"
}
catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test kotorcli shim imports
Write-Host "`n3. Testing kotorcli shim imports..." -ForegroundColor Yellow
$env:PYTHONPATH = "Tools\KotorCLI\src;Libraries\PyKotor\src;Libraries\Utility\src"
try {
    python -c "from kotorcli.__main__ import main; print('✓ kotorcli.__main__.main imported')"
}
catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test kotordiff shim imports
Write-Host "`n4. Testing kotordiff shim imports..." -ForegroundColor Yellow
$env:PYTHONPATH = "Tools\KotorDiff\src;Libraries\PyKotor\src;Libraries\Utility\src"
try {
    python -c "from kotordiff.__main__ import main; print('✓ kotordiff.__main__.main imported')"
}
catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test module execution
Write-Host "`n5. Testing module execution..." -ForegroundColor Yellow
$env:PYTHONPATH = "Libraries\PyKotor\src"
try {
    $result = python -m pykotor --help 2>&1 | Select-Object -First 3
    if ($result -match "usage|help|pykotor") {
        Write-Host "✓ python -m pykotor works" -ForegroundColor Green
    }
    else {
        Write-Host "✗ python -m pykotor output unexpected" -ForegroundColor Red
    }
}
catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Testing Build Configuration ===" -ForegroundColor Cyan

# Check pyproject.toml entry points
Write-Host "`n6. Checking pyproject.toml entry points..." -ForegroundColor Yellow
$pyproject = Get-Content "Libraries\PyKotor\pyproject.toml" -Raw
if ($pyproject -match 'pykotor = "pykotor\.cli\.__main__:main"') {
    Write-Host "✓ pykotor entry point found" -ForegroundColor Green
}
else {
    Write-Host "✗ pykotor entry point missing" -ForegroundColor Red
}
if ($pyproject -match 'pykotorcli = "pykotor\.cli\.__main__:main"') {
    Write-Host "✓ pykotorcli entry point found" -ForegroundColor Green
}
else {
    Write-Host "✗ pykotorcli entry point missing" -ForegroundColor Red
}

# Check setup.py entry points
Write-Host "`n7. Checking setup.py entry points..." -ForegroundColor Yellow
$setup = Get-Content "Libraries\PyKotor\setup.py" -Raw
if ($setup -match 'pykotor=pykotor\.cli\.__main__:main') {
    Write-Host "✓ pykotor entry point in setup.py" -ForegroundColor Green
}
else {
    Write-Host "✗ pykotor entry point missing in setup.py" -ForegroundColor Red
}

# Check kotorcli pyproject.toml
Write-Host "`n8. Checking kotorcli pyproject.toml..." -ForegroundColor Yellow
$kotorcli_pyproject = Get-Content "Tools\KotorCLI\pyproject.toml" -Raw
if ($kotorcli_pyproject -match 'kotorcli = "kotorcli\.__main__:main"') {
    Write-Host "✓ kotorcli entry point found" -ForegroundColor Green
}
else {
    Write-Host "✗ kotorcli entry point missing" -ForegroundColor Red
}
if ($kotorcli_pyproject -match 'pykotor>=2\.1\.0') {
    Write-Host "✓ kotorcli depends on pykotor>=2.1.0" -ForegroundColor Green
}
else {
    Write-Host "✗ kotorcli dependency version incorrect" -ForegroundColor Red
}

# Check kotordiff pyproject.toml
Write-Host "`n9. Checking kotordiff pyproject.toml..." -ForegroundColor Yellow
$kotordiff_pyproject = Get-Content "Tools\KotorDiff\pyproject.toml" -Raw
if ($kotordiff_pyproject -match 'kotordiff = "kotordiff\.__main__:main"') {
    Write-Host "✓ kotordiff entry point found" -ForegroundColor Green
}
else {
    Write-Host "✗ kotordiff entry point missing" -ForegroundColor Red
}
if ($kotordiff_pyproject -match 'pykotor>=2\.0\.2') {
    Write-Host "✓ kotordiff depends on pykotor" -ForegroundColor Green
}
else {
    Write-Host "✗ kotordiff dependency missing" -ForegroundColor Red
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "All tests completed. Check output above for any failures." -ForegroundColor Yellow
