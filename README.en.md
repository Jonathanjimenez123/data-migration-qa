# Data Migration QA

**A portfolio project for validating and reconciling data between source and target systems.**

Data Migration QA is a personal project focused on data quality assurance and test automation. It helps compare datasets, identify discrepancies, and inspect reconciliation results through a web interface and an API.

> Demonstration project using fictional data. It is not intended for real personal or financial data without an additional security and requirements review.

## Live demo and links

- **Web application:** https://data-migration-qa.vercel.app/
- **API:** https://data-migration-qa-api.onrender.com/
- **Interactive API documentation:** https://data-migration-qa-api.onrender.com/docs
- **Health check:** https://data-migration-qa-api.onrender.com/api/v1/health
- **Source code:** https://github.com/Jonathanjimenez123/data-migration-qa

Free-tier services may take a short time to respond after being idle.

## The problem

During data migration, records may be missing, unexpected records may appear, or field values may differ between source and target systems. This project aims to make those discrepancies visible through repeatable checks.

## Features

- Source-to-target data comparison.
- Detection of missing and unexpected records.
- Identification of field-level differences.
- Reconciliation result visualization.
- REST API with Swagger/OpenAPI documentation.
- Automated API tests.
- Separate deployment of the frontend and API.

The checks available depend on the current configuration and deployed version.

## Technology stack

| Area | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| API | Python, FastAPI |
| Database | PostgreSQL |
| Testing | pytest |
| Frontend hosting | Vercel |
| API hosting | Render |
| Managed database | Neon PostgreSQL |

## Architecture

```text
User
  |
  v
React + Vite frontend (Vercel)
  |
  v
FastAPI REST API (Render)
  |
  v
Managed PostgreSQL (Neon)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for details.

## Try the demo

1. Open the [web application](https://data-migration-qa.vercel.app/).
2. Upload demonstration CSV files if the interface provides that option.
3. Run the reconciliation.
4. Review the matching records and discrepancies shown in the results.

Use fictional sample data only. Check the columns expected by the current interface before uploading your own files.

## Run locally

### Prerequisites

- Git
- Node.js and npm
- A Python version compatible with the project dependencies
- PostgreSQL for features that require a database

### Frontend

In PowerShell:

```powershell
Set-Location "C:\data-migration-qa\apps\web"
npm install
npm run dev
```

To validate a production build:

```powershell
npm run build
```

### API and tests

From the repository root, activate the Python virtual environment if it already exists. The local test command used for this project was:

```powershell
Set-Location "C:\data-migration-qa"
$env:PYTHONPATH="$PWD\apps\api"
& ".\apps\api\.venv\Scripts\python.exe" -m pytest -q apps\api\tests
```

This command assumes that the virtual environment exists at `apps\api\.venv` and the dependencies are installed. For a fresh setup, check the repository's dependency files and API configuration.

## Further documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md)
- [Screenshots](docs/SCREENSHOTS.md)
- [README en español](README.md)

## Screenshots

Real application screenshots will be added under `docs/screenshots/`. See [`docs/SCREENSHOTS.md`](docs/SCREENSHOTS.md). No simulated images are presented as actual application screenshots.

## Security and sample data

- Never commit `.env` files, passwords, API keys, tokens, or database connection strings.
- Do not use real personal or financial data in public CSV samples, reports, or screenshots.
- Keep credentials in each hosting provider's environment variables.
- Review `git status` and staged files before committing changes.

## About this project

A personal portfolio project built to practice data validation, automated testing, API development, and web deployment. Capabilities should be assessed against the current source code and tests; this project is not represented as paid employment experience.
