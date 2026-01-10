# How to Test Atlas Data Pipeline Platform

Quick guide to test the Week 3 features: PII detection + quality validation.

---

## Option 1: Quick Test Script (Easiest) ⚡

### Step 1: Make sure API is running
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

Keep this terminal open. Open a NEW terminal for testing.

### Step 2: Run test script with your CSV
```bash
/tmp/test_atlas.sh /path/to/your_file.csv
```

**Example:**
```bash
/tmp/test_atlas.sh ~/Desktop/customers.csv
```

That's it! The script will:
- Upload your CSV
- Show quality scores (6 dimensions)
- Show PII detections
- Give you URLs to see full details

---

## Option 2: Browser UI (Most Visual) 🌐

### Step 1: Open interactive API docs
```bash
open http://localhost:8000/docs
```

### Step 2: Upload CSV
1. Find the **`POST /pipeline/run`** endpoint
2. Click **"Try it out"**
3. Click **"Choose File"** and select your CSV
4. Enter a **dataset_name** (e.g., "test_data")
5. Click **"Execute"**
6. Copy the **run_id** from the response

### Step 3: Get results
1. Find **`GET /quality/metrics/{run_id}`**
2. Click **"Try it out"**
3. Paste your **run_id**
4. Click **"Execute"**
5. See all 6 quality dimensions!

Repeat for:
- **`GET /quality/pii-report/{run_id}`** - See PII detections
- **`GET /compliance/report/{run_id}`** - See compliance status

---

## Option 3: Command Line (Most Control) 💻

### Upload CSV
```bash
curl -X POST http://localhost:8000/pipeline/run \
  -F "file=@/path/to/your_file.csv" \
  -F "dataset_name=my_test"
```

Copy the `run_id` from the response.

### Get Quality Metrics (All 6 Dimensions)
```bash
curl http://localhost:8000/quality/metrics/{run_id} | python3 -m json.tool
```

### Get PII Report
```bash
curl http://localhost:8000/quality/pii-report/{run_id} | python3 -m json.tool
```

### Get Compliance Report
```bash
curl http://localhost:8000/compliance/report/{run_id} | python3 -m json.tool
```

---

## Option 4: Create Sample Data 📝

Don't have a CSV? Create one:

```bash
cat > ~/Desktop/test_data.csv << 'EOF'
name,email,phone,city,status
John Doe,john@example.com,+1234567890,Copenhagen,active
Jane Smith,jane@test.com,+9876543210,Aarhus,active
Bob Wilson,invalid-email,555-1234,Oslo,inactive
EOF
```

Then test with:
```bash
/tmp/test_atlas.sh ~/Desktop/test_data.csv
```

---

## What You'll See

### Quality Metrics (6 Dimensions)
- **Completeness**: % of cells with data (target: >95%)
- **Uniqueness**: % of non-duplicate rows (target: >98%)
- **Timeliness**: Date freshness (target: <7 days old)
- **Validity**: % of correctly formatted data (target: >90%)
- **Accuracy**: Statistical outlier detection (target: >90%)
- **Consistency**: Cross-field validation (target: >90%)

### PII Detection
- **EMAIL_ADDRESS**: Email addresses
- **PERSON**: Names (first, last, full)
- **PHONE_NUMBER**: Phone numbers
- **CREDIT_CARD**: Credit card numbers
- **DK_CPR**: Danish CPR numbers
- **DATE_TIME**: Date/time fields
- Plus 20+ more types

### Confidence Scores
- **100%**: Definite match (regex patterns)
- **85%+**: High confidence (ML detection)
- **50-85%**: Medium confidence
- **<50%**: Low confidence (review needed)

---

## Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
lsof -ti :8000 | xargs kill -9

# Then restart
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

### "Module not found" errors
```bash
# Reinstall Week 3 dependencies
pip install presidio-analyzer presidio-anonymizer spacy soda-core-postgres soda-core-scientific
python3 -m spacy download en_core_web_sm
python3 -m spacy download da_core_news_sm
```

### Can't find test script
```bash
# The script is at /tmp/test_atlas.sh
# If missing, copy from this file and save it
```

---

## Real-World Test Cases

### Test Case 1: Customer Data
```csv
customer_id,name,email,phone,address,city,zipcode
C001,John Smith,john@gmail.com,+4512345678,Main St 123,Copenhagen,1000
```

**Expected Results**:
- PII Found: name, email, phone, address
- Quality: 100% (all fields complete)

### Test Case 2: Data with Issues
```csv
name,email,age,city
Alice,alice@test.com,25,Berlin
Bob,invalid-email,invalid,,
```

**Expected Results**:
- PII Found: name, email
- Quality: ~83% (missing city, invalid email, invalid age)
- Issues Detected: 3

### Test Case 3: Financial Data
```csv
name,credit_card,cpr_number,account
Anders,4532123456789012,010190-1234,DK123456
```

**Expected Results**:
- PII Found: name, credit_card, cpr_number
- High-sensitivity data detected
- GDPR compliance warnings

---

## Quick Tips

- **Start simple**: Test with 5-10 rows first
- **Check logs**: If API crashes, check `/tmp/atlas_week3_api.log`
- **Use docs**: The interactive docs at `/docs` are very helpful
- **Mix data types**: Test with text, numbers, dates for best results
- **Include issues**: Add intentional errors to test detection

---

## Next Steps After Testing

Once you've confirmed Week 3 works:

1. **Use with real data**: Upload your actual datasets
2. **Continue to Week 4**: Add database connectors
3. **Review documentation**: See `docs/IMPLEMENTATION_PLAN.md`
4. **Customize thresholds**: Adjust quality thresholds in code

---

**Need help?** Check the logs or ask for assistance!
