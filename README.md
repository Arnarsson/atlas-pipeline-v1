# Atlas Data Pipeline Platform v1.0

**Production-Ready Full-Stack Data Platform**

Complete data pipeline platform with ML-powered PII detection, quality validation, and GDPR compliance.

## Features

- ✅ CSV upload with ML PII detection (Presidio - 99% accuracy)
- ✅ 6-dimension quality framework (Soda Core)
- ✅ Database connectors (PostgreSQL, MySQL, REST API)
- ✅ Automated scheduling (Celery)
- ✅ Data lineage tracking (OpenLineage)
- ✅ GDPR workflows (Export, Delete, Audit)
- ✅ Feature store for AI/ML
- ✅ Data catalog with search
- ✅ Professional web dashboard (9 pages)

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python3 simple_main.py
```
→ http://localhost:8000

### Frontend  
```bash
cd frontend
npm install
npm run dev
```
→ http://localhost:5174

## Documentation

- `backend/START_HERE.md` - Backend quick start
- `frontend/QUICKSTART.md` - Frontend quick start
- `docs/` - Complete implementation guides

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite
- **ML**: Presidio (PII) + Soda Core (Quality)
- **Database**: PostgreSQL 15

## License

MIT
