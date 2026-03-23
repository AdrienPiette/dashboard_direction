# Hospital Data Lab

Streamlit application for hospital data import, preparation, exploration, RPM parsing and machine learning experimentation.

## Features

- CSV and Excel upload
- RPM text import for Belgian fixed-width or delimited exports
- Data cleaning and normalization workflow
- Executive dashboard page
- Clustering lab with K-Means, Agglomerative and DBSCAN
- Export to CSV, Excel and SQLite

## Project structure

- `App.py`: home page
- `pages/0_Import_RPM.py`: RPM text import
- `pages/1_Analyse_des_donnees.py`: data preparation and profiling
- `pages/2_Test_de_modeles.py`: clustering lab
- `pages/3_Dashboard_direction.py`: management dashboard
- `utils/data_loader.py`: shared UI and data preparation utilities
- `utils/rpm_parser.py`: RPM parsing and export helpers

## Local installation on Windows

### 1. Install Python

Use Python 3.11 or 3.12.

Check:

```powershell
python --version
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 4. Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the app

```powershell
streamlit run App.py
```

The app will open on [http://localhost:8501](http://localhost:8501).

## One-command local setup

PowerShell scripts are provided:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_local.ps1
powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1
```

## Company deployment options

### Option 1: Internal Windows server

Recommended when your company already manages Windows servers.

1. Install Python 3.11 or 3.12 on the server.
2. Copy the project folder.
3. Run `scripts\install_local.ps1`.
4. Start the app with `scripts\run_local.ps1`.
5. Put Nginx, IIS or your internal reverse proxy in front of port `8501`.

Recommended reverse proxy target:

- App host: `http://127.0.0.1:8501`
- Public internal URL example: `https://hospital-data-lab.intra`

### Option 2: Docker deployment

Recommended when your company uses containers.

Build the image:

```powershell
docker build -t hospital-data-lab .
```

Run the container:

```powershell
docker run -d --name hospital-data-lab -p 8501:8501 hospital-data-lab
```

Or use Compose:

```powershell
docker compose up -d --build
```

## Security and company hardening

For a real company deployment, put the app behind your internal authentication layer:

- Azure AD / Entra ID
- IIS authentication
- Nginx with SSO
- company VPN only

This app currently stores uploaded data in Streamlit session memory, not in a permanent database. That is usually safer for a first internal deployment.

## Notes

- Do not commit real hospital secrets to `.streamlit/secrets.toml`.
- The `data/` folder currently contains sample files. Replace them with approved demo data only.
- If you deploy on a shared server, review access rights on the project folder.
