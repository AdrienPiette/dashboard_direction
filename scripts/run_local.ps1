$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Virtual environment not found. Run scripts\install_local.ps1 first."
}

& .\.venv\Scripts\python.exe -m streamlit run App.py
