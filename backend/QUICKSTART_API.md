# Atlas Data Pipeline - Quick Start Guide

## 🚀 5-Minute Setup

```bash
# 1. Navigate to project
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api

# 2. Install dependencies (one-time)
pip install -r requirements-simple.txt

# 3. Start the API server
python3 simple_main.py

# Server starts on http://localhost:8000
```

## ✅ Test It Works

```bash
# Health check
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## 📤 Upload and Process Data

```bash
# Create a test CSV file
cat > sample.csv << 'EOF'
name,email,phone,age,city
John Doe,john@example.com,555-1234,30,NYC
Jane Smith,jane@company.com,555-5678,25,LA
EOF

# Upload and process
curl -X POST "http://localhost:8000/pipeline/run" \
  -F "file=@sample.csv" \
  -F "dataset_name=customers"

# Save the run_id from response
```

## 📊 Check Results

```bash
# Replace {run_id} with actual ID from upload response

# 1. Check status
curl http://localhost:8000/pipeline/status/{run_id} | python3 -m json.tool

# 2. Get quality metrics
curl http://localhost:8000/quality/metrics/{run_id} | python3 -m json.tool

# 3. Get PII report
curl http://localhost:8000/quality/pii-report/{run_id} | python3 -m json.tool

# 4. Get compliance report
curl http://localhost:8000/compliance/report/{run_id} | python3 -m json.tool
```

## 🧪 Run Full Test Suite

```bash
./test_api.sh
```

## 📖 What You Get

- ✅ **CSV Processing** - Upload and analyze CSV files
- ✅ **PII Detection** - Find emails, phones, SSNs, credit cards, etc.
- ✅ **Quality Metrics** - Completeness, validity, consistency scores
- ✅ **Compliance Reports** - Combined PII + quality analysis
- ✅ **Real-time Status** - Track pipeline progress
- ✅ **Interactive Docs** - Auto-generated API documentation

## 🎯 Key Features

### 1. Explore Layer (Bronze)
- CSV data ingestion
- Type detection
- Row/column counting

### 2. Chart Layer (Silver)
- **PII Detection**: emails, phones, zipcodes, SSNs, credit cards, IPs
- **Quality Checks**: missing values, duplicates, data validity
- **Scoring**: 0-100% for completeness, validity, consistency

### 3. Compliance
- Non-compliant: PII found
- Warning: Quality below 70%
- Compliant: Clean data

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | API info |
| `/docs` | GET | Swagger UI |
| `/pipeline/run` | POST | Upload CSV and start pipeline |
| `/pipeline/status/{id}` | GET | Check pipeline status |
| `/pipeline/runs` | GET | List all runs |
| `/quality/metrics/{id}` | GET | Get quality scores |
| `/quality/pii-report/{id}` | GET | Get PII findings |
| `/compliance/report/{id}` | GET | Get compliance status |

## 📝 Example Response

```json
{
  "run_id": "abc123",
  "status": "completed",
  "results": {
    "explore": {
      "rows": 5,
      "columns": 3
    },
    "pii": {
      "findings": [
        {
          "column": "email",
          "type": "email",
          "match_count": 5,
          "percentage": 1.0
        }
      ]
    },
    "quality": {
      "overall_score": 0.98,
      "completeness_score": 1.0,
      "validity_score": 1.0,
      "consistency_score": 0.95
    }
  }
}
```

## 🛠️ Troubleshooting

**Port already in use?**
```bash
pkill -f simple_main.py
python3 simple_main.py
```

**Module not found?**
```bash
pip install -r requirements-simple.txt
```

## 📚 Full Documentation

See [PHASE1_WEEK2_README.md](PHASE1_WEEK2_README.md) for complete documentation.

## 🎉 Success!

You now have a working data pipeline API that:
- Processes CSV files
- Detects PII
- Checks data quality
- Generates compliance reports

**Next**: Integrate with database (Phase 1 Week 3)
