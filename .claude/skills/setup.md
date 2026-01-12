# Setup Skill

Install all dependencies and configure the Atlas Pipeline environment.

## When to Use
- When starting fresh development
- After cloning the repository
- When encountering ModuleNotFoundError

## Instructions

### 1. Install Backend Dependencies

```bash
cd /home/user/atlas-pipeline-v1/backend
pip install fastapi uvicorn python-multipart pydantic pydantic-settings python-dotenv
pip install pandas httpx aiohttp aiomysql asyncpg
pip install loguru tenacity celery redis prometheus-client
pip install sqlmodel sqlalchemy email-validator
```

### 2. Install Frontend Dependencies

```bash
cd /home/user/atlas-pipeline-v1/frontend
npm install
```

### 3. Verify Installation

Test that the backend can import without errors:
```bash
cd /home/user/atlas-pipeline-v1/backend
python -c "from app.connectors.registry import ConnectorRegistry; print('Backend imports OK')"
```

Test that frontend builds:
```bash
cd /home/user/atlas-pipeline-v1/frontend
npm run build
```

## Known Issues

### Optional Connectors
Google Sheets and Salesforce connectors require additional dependencies that may have cryptography issues. These are made optional in `registry.py` and will gracefully fall back if unavailable.

### PyAirbyte
PyAirbyte is optional. Install with `pip install airbyte` for full connector support. The system works in degraded mode without it.

### Presidio (PII Detection)
Presidio requires spacy models. Install with:
```bash
pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg
```
