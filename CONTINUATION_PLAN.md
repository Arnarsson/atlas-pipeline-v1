# Atlas Data Pipeline - Continuation Plan
**Date**: January 11, 2026
**Current Status**: 84% Complete (Atlas Data Pipeline Standard)
**Recent Work**: 3 PRs with codecs collaboration (normalization, API fixes, dashboard stats)

---

## 🎯 Phase 1: Integration & Consolidation (IMMEDIATE)

### **1.1 Merge Outstanding Work** ⏱️ 30 minutes
**Priority**: CRITICAL

Current state:
- ✅ **PR/1** (`pr/1`): Data normalization - Ready to merge
- ✅ **PR/2** (`pr/2`): API contract fixes - Ready to merge
- ✅ **Dashboard Stats** (`feature/dashboard-stats`): Dashboard endpoint - **MUST MERGE**

**Actions**:
```bash
# Step 1: Merge dashboard-stats (has latest dashboard.py)
git checkout feature/api-contract-fix-and-tests
git merge feature/dashboard-stats

# Step 2: Cherry-pick normalization improvements from pr/1
git cherry-pick c6d5782  # Data normalization commit

# Step 3: Verify no conflicts with pr/2 work (already on current branch)
git log --oneline -5
```

**Expected Outcome**:
- Single unified branch with all improvements
- Dashboard stats endpoint functional
- Data normalization applied
- API contracts aligned

---

### **1.2 Comprehensive Testing** ⏱️ 45 minutes
**Priority**: HIGH

**Backend Tests**:
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
./scripts/verify-setup.sh
```

**Frontend E2E Tests**:
```bash
cd frontend
npm run test:e2e
```

**Integration Test**:
```bash
# 1. Start backend
python3 simple_main.py

# 2. Start frontend (new terminal)
cd frontend && npm run dev

# 3. Upload test CSV and verify:
#    - All 6 quality dimensions display
#    - PII detection works
#    - Dashboard stats load correctly
#    - No console errors
```

**Verification Checklist**:
- [ ] Backend: 82/82 tests passing
- [ ] Frontend: 122+ E2E tests passing
- [ ] Dashboard stats endpoint returns data
- [ ] CSV upload → Quality + PII analysis works
- [ ] No console TypeError errors
- [ ] All 9 pages navigate correctly

---

### **1.3 Update Documentation** ⏱️ 20 minutes
**Priority**: MEDIUM

**Update CLAUDE.md**:
- ✅ Mark dashboard stats as FIXED (no longer 404)
- ✅ Update test count (may have increased)
- ✅ Document new normalization features
- ✅ Update "Recent Updates" section with merge info

**Create MERGE_NOTES.md**:
```markdown
# Branch Merge Summary - Jan 11, 2026

## Merged Branches
1. feature/dashboard-stats (5e67503) - Dashboard stats endpoint
2. pr/1 data normalization (c6d5782) - Client normalization
3. pr/2 already integrated - API contract fixes

## New Features
- /dashboard/stats endpoint with 5 metrics
- Comprehensive data normalization layer
- Enhanced error handling with ErrorBoundary

## Testing Updates
- Added test_dashboard.py (backend)
- Enhanced E2E tests for new features
```

---

## 🚀 Phase 2: Fill Critical Gaps (16% → 90%)

### **2.1 Advanced Connectors** ⏱️ 8-12 hours
**Priority**: HIGH (adds 6% to completion)

**Target**: Add 2 high-value connectors

#### **Option A: Salesforce CRM Connector**
**Business Value**: HIGH (CRM data is critical for analytics)

```python
# backend/app/connectors/salesforce_connector.py
class SalesforceConnector:
    """Salesforce CRM connector with OAuth2."""

    def __init__(self, config):
        self.instance_url = config["instance_url"]
        self.access_token = config["access_token"]

    async def fetch_data(self, object_type: str):
        # Fetch Accounts, Contacts, Opportunities, etc.
        # Use Salesforce REST API
        # Handle pagination and rate limits
```

**Features**:
- OAuth2 authentication
- Fetch standard objects (Account, Contact, Opportunity, Lead)
- Custom object support
- Field mapping to Atlas schema
- Incremental sync based on `LastModifiedDate`

**Estimated**: 6 hours

---

#### **Option B: Google Sheets Connector**
**Business Value**: MEDIUM-HIGH (many businesses use Sheets as DB)

```python
# backend/app/connectors/google_sheets_connector.py
class GoogleSheetsConnector:
    """Google Sheets connector with service account auth."""

    def __init__(self, config):
        self.spreadsheet_id = config["spreadsheet_id"]
        self.credentials = config["service_account_json"]

    async def fetch_data(self, sheet_name: str):
        # Fetch sheet data via Google Sheets API
        # Auto-detect column types
        # Handle multiple sheets
```

**Features**:
- Service account or OAuth2 authentication
- Multi-sheet support
- Auto-detect headers and data types
- Real-time updates via webhooks (optional)
- Export capability (read + write)

**Estimated**: 4 hours

---

### **2.2 Real-time Streaming (Kafka)** ⏱️ 12-16 hours
**Priority**: MEDIUM (adds 4% to completion)

**Goal**: Enable real-time data ingestion

```python
# backend/app/streaming/kafka_consumer.py
class KafkaStreamProcessor:
    """Process real-time data from Kafka topics."""

    async def consume_topic(self, topic: str):
        # Consume messages from Kafka
        # Apply PII detection in real-time
        # Stream to Explore layer
        # Trigger quality checks on batches
```

**Features**:
- Kafka topic subscription
- Real-time PII masking
- Micro-batch quality validation (every 100 records)
- Stream to Explore → Chart → Navigate
- Offset management and recovery

**Estimated**: 12 hours

---

### **2.3 Advanced RBAC** ⏱️ 6-8 hours
**Priority**: MEDIUM (adds 3% to completion)

**Goal**: Multi-tenant access control

```python
# backend/app/auth/rbac.py
class RBACManager:
    """Role-based access control for datasets and features."""

    ROLES = {
        "admin": ["read", "write", "delete", "manage_users"],
        "data_engineer": ["read", "write", "run_pipelines"],
        "analyst": ["read", "export"],
        "viewer": ["read"]
    }
```

**Features**:
- JWT-based authentication
- Role hierarchy (Admin > Engineer > Analyst > Viewer)
- Dataset-level permissions
- Feature store access control
- Audit logging for all access

**Estimated**: 8 hours

---

### **2.4 ML Model Tracking** ⏱️ 6-8 hours
**Priority**: MEDIUM (adds 3% to completion)

**Goal**: Track ML models trained on Atlas data

```python
# backend/app/ml/model_registry.py
class ModelRegistry:
    """Register and track ML models."""

    async def register_model(self, model_info: dict):
        # Register model with metadata
        # Link to feature group version
        # Track performance metrics
        # Store model artifacts (S3/GCS)
```

**Features**:
- Model versioning (semantic versioning)
- Link models to feature group versions
- Performance metrics tracking (accuracy, F1, etc.)
- A/B test tracking
- Model lineage (which data produced which model)

**Estimated**: 6 hours

---

## 📊 Phase 3: Production Hardening (90% → 95%)

### **3.1 Monitoring & Observability** ⏱️ 8-10 hours
**Priority**: HIGH

**Components**:
1. **Prometheus Metrics**
   - Pipeline execution time
   - Quality score trends
   - PII detection counts
   - API response times
   - Database connection pool stats

2. **Grafana Dashboards**
   - System health dashboard
   - Data quality trends
   - Pipeline performance
   - User activity
   - Cost tracking (if cloud-based)

3. **Alerting**
   - Quality score drops below threshold
   - Pipeline failures
   - High PII detection rates
   - API errors spike
   - Database connection issues

**Estimated**: 10 hours

---

### **3.2 CI/CD Pipeline** ⏱️ 6-8 hours
**Priority**: MEDIUM-HIGH

**GitHub Actions Workflow**:
```yaml
# .github/workflows/atlas-ci.yml
name: Atlas Pipeline CI/CD

on: [push, pull_request]

jobs:
  test:
    - Backend tests (pytest)
    - Frontend tests (Playwright)
    - Integration tests

  build:
    - Docker image build
    - Push to registry

  deploy:
    - Deploy to staging (auto)
    - Deploy to production (manual approval)
```

**Features**:
- Automated testing on every PR
- Docker image building
- Automated deployment to staging
- Manual approval for production
- Rollback capability

**Estimated**: 8 hours

---

### **3.3 Backup & Disaster Recovery** ⏱️ 4-6 hours
**Priority**: MEDIUM

**Components**:
1. **Database Backups**
   - Automated daily PostgreSQL dumps
   - Point-in-time recovery (WAL archiving)
   - Backup retention policy (30 days)

2. **Data Layer Backups**
   - Explore layer (raw data) - S3/GCS backup
   - Feature store versions - immutable storage
   - Configuration backups

3. **Recovery Procedures**
   - Documented recovery steps
   - Recovery time objective (RTO): < 4 hours
   - Recovery point objective (RPO): < 1 hour

**Estimated**: 6 hours

---

## 🎯 Phase 4: Advanced Features (95% → 100%)

### **4.1 Data Catalog Enhancements** ⏱️ 4-6 hours
**Priority**: LOW-MEDIUM

**New Features**:
- **Smart Search**: Full-text search across schemas, descriptions, tags
- **Data Lineage Visualization**: Interactive graph (D3.js/Cytoscape)
- **Usage Analytics**: Track which datasets are most queried
- **Data Profiling**: Statistical summaries, histograms, distributions
- **Collaboration**: Comments, annotations, dataset ratings

**Estimated**: 6 hours

---

### **4.2 Advanced Quality Rules** ⏱️ 6-8 hours
**Priority**: LOW-MEDIUM

**Custom Rules Engine**:
```python
# backend/app/pipeline/quality/custom_rules.py
class CustomQualityRule:
    """Define custom quality validation rules."""

    def __init__(self, rule_config: dict):
        self.name = rule_config["name"]
        self.condition = rule_config["condition"]
        self.threshold = rule_config["threshold"]

    async def validate(self, data: pd.DataFrame) -> bool:
        # Evaluate custom condition
        # Return pass/fail with details
```

**Features**:
- User-defined validation rules
- SQL-like condition syntax
- Cross-column validation
- Time-series anomaly detection
- Automated remediation suggestions

**Estimated**: 8 hours

---

### **4.3 API Gateway & Rate Limiting** ⏱️ 4-6 hours
**Priority**: LOW

**Components**:
- API key management
- Rate limiting (per user/API key)
- Request throttling
- Usage quotas
- API analytics dashboard

**Estimated**: 6 hours

---

## 📋 Recommended Execution Order

### **Sprint 1: Integration (Week 1)** ⏱️ ~8 hours
1. ✅ Merge all branches (1.1)
2. ✅ Comprehensive testing (1.2)
3. ✅ Update documentation (1.3)
4. 🚀 Add Salesforce connector (2.1A)
5. 🚀 Add Google Sheets connector (2.1B)

**Outcome**: Clean codebase, 2 new connectors → **90% complete**

---

### **Sprint 2: Production Ready (Week 2)** ⏱️ ~12 hours
1. 🚀 Monitoring & observability (3.1)
2. 🚀 CI/CD pipeline (3.2)
3. 🚀 Backup & recovery (3.3)
4. 🚀 Advanced RBAC (2.3)

**Outcome**: Production-grade system → **95% complete**

---

### **Sprint 3: Advanced (Week 3)** ⏱️ ~16 hours
1. 🚀 Real-time streaming (2.2)
2. 🚀 ML model tracking (2.4)
3. 🚀 Data catalog enhancements (4.1)
4. 🚀 Custom quality rules (4.2)

**Outcome**: Enterprise-ready platform → **100% complete**

---

## 🎯 Alternative: Quick Wins Path (1 Week)

If time is limited, focus on **high-impact, low-effort** features:

### **Day 1-2: Merge & Test** ⏱️ 4 hours
- Merge branches
- Test everything
- Update docs

### **Day 3-4: Top 2 Connectors** ⏱️ 10 hours
- Google Sheets (easier, 4h)
- Salesforce (high value, 6h)

### **Day 5: Monitoring** ⏱️ 6 hours
- Basic Prometheus metrics
- Simple Grafana dashboard
- Critical alerts

**Total**: 20 hours → **92% complete** with high-value additions

---

## 📊 Completion Roadmap

| Phase | Features | Hours | Completion % |
|-------|----------|-------|--------------|
| **Current** | Core platform, 3 connectors, GDPR, Quality, PII | - | **84%** |
| **Phase 1** | Merge branches, testing | 2h | **84%** (consolidated) |
| **Phase 2** | +2 connectors, RBAC, ML tracking | 20h | **90%** |
| **Phase 3** | Monitoring, CI/CD, backups | 24h | **95%** |
| **Phase 4** | Streaming, advanced features | 30h | **100%** |

**Total Time to 100%**: ~76 hours (~2-3 weeks at 30h/week)

---

## 🎯 Success Metrics

### **Technical Metrics**
- [ ] All tests passing (backend + frontend)
- [ ] API response time < 200ms (p95)
- [ ] Zero console errors in frontend
- [ ] Database queries optimized (< 100ms)
- [ ] PII detection accuracy > 99%

### **Feature Metrics**
- [ ] 5+ data connectors operational
- [ ] RBAC protecting all endpoints
- [ ] ML model tracking in use
- [ ] Real-time streaming operational
- [ ] Monitoring dashboards deployed

### **Production Metrics**
- [ ] CI/CD pipeline automated
- [ ] Backups running daily
- [ ] Alerts configured and tested
- [ ] Documentation complete
- [ ] Deployment runbooks created

---

## 📝 Next Steps (RIGHT NOW)

```bash
# 1. Merge dashboard-stats branch
git merge feature/dashboard-stats

# 2. Test the system
cd backend && python3 simple_main.py
cd frontend && npm run dev

# 3. Verify dashboard stats endpoint
curl http://localhost:8000/dashboard/stats | jq

# 4. Choose next feature from Phase 2
#    Recommendation: Start with Google Sheets connector (easiest, 4h)
```

---

**Ready to continue! Which phase should we tackle first?** 🚀
