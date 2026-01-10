# Atlas Dashboard E2E Tests - Complete Index

## Quick Navigation

- **New to testing?** → Start with [QUICK_START.md](QUICK_START.md)
- **Need full details?** → Read [README.md](README.md)
- **Want statistics?** → See [TEST_SUMMARY.md](TEST_SUMMARY.md)
- **Ready to run?** → Execute `./verify-setup.sh` then `npm run test:e2e:ui`

---

## File Structure

```
tests/e2e/
├── 📖 Documentation
│   ├── INDEX.md              ← You are here
│   ├── README.md             ← Comprehensive guide (400+ lines)
│   ├── QUICK_START.md        ← Quick reference (280+ lines)
│   └── TEST_SUMMARY.md       ← Statistics & metrics
│
├── 🧪 Test Suites (10 files, 57 tests)
│   ├── 01-navigation.spec.ts      (6 tests)  Navigation, sidebar, routing
│   ├── 02-csv-upload.spec.ts      (6 tests)  File upload, quality, PII
│   ├── 03-connectors.spec.ts      (7 tests)  Connector management
│   ├── 04-quality-reports.spec.ts (6 tests)  Reports, search, filters
│   ├── 05-gdpr.spec.ts            (6 tests)  GDPR workflows
│   ├── 06-catalog.spec.ts         (6 tests)  Data catalog
│   ├── 07-features.spec.ts        (6 tests)  Feature store
│   ├── 08-user-journey.spec.ts    (5 tests)  End-to-end workflows
│   ├── 09-performance.spec.ts     (6 tests)  Performance benchmarks
│   └── 10-visual.spec.ts          (8 tests)  Visual regression
│
├── 🛠️ Utilities
│   └── helpers/
│       └── setup.ts               Test utilities & CSV generation
│
└── 🚀 Scripts
    ├── run-tests.sh               Full test runner with checks
    └── verify-setup.sh            Setup verification script
```

---

## Quick Command Reference

### Run Tests
```bash
npm run test:e2e              # Run all tests (headless)
npm run test:e2e:ui           # Interactive UI mode ⭐ Recommended
npm run test:e2e:debug        # Step-by-step debugger
npm run test:e2e:headed       # Run with visible browser
npm run test:e2e:chromium     # Chromium only
npm run test:e2e:firefox      # Firefox only
npm run test:e2e:report       # View last test report
```

### Verify Setup
```bash
./tests/e2e/verify-setup.sh   # Check if ready to run
./tests/e2e/run-tests.sh      # Check services + run tests
```

### Specific Tests
```bash
npx playwright test 02-csv-upload.spec.ts           # One file
npx playwright test -g "should upload CSV"          # By test name
npx playwright test --headed --slow-mo=1000         # Slow motion
npx playwright test --update-snapshots              # Update visuals
```

---

## Test Coverage Overview

### Pages (9/9 = 100%)
✅ Dashboard • ✅ Upload • ✅ Connectors • ✅ Quality Reports • ✅ PII
✅ Data Catalog • ✅ Feature Store • ✅ GDPR • ✅ Lineage

### Test Categories
- **Navigation**: 6 tests - Page loading, sidebar, routing
- **File Upload**: 6 tests - CSV upload, quality metrics, PII detection
- **Connectors**: 7 tests - CRUD operations, validation
- **Reports**: 6 tests - Search, filters, display
- **GDPR**: 6 tests - Request workflows, validation
- **Catalog**: 6 tests - Datasets, search, metadata
- **Features**: 6 tests - Feature store operations
- **User Journeys**: 5 tests - Complete workflows
- **Performance**: 6 tests - Load times, benchmarks
- **Visual**: 8 tests - Screenshots, responsive design

### Performance Benchmarks
- Dashboard load: <3 seconds
- Page navigation: <1 second
- Upload render: <2 seconds
- API health: <500ms
- Large CSV (1000 rows): <30 seconds

---

## Prerequisites Checklist

### Required Services
- [ ] Backend API running on `http://localhost:8000`
  - Start: `cd /Users/sven/Desktop/MCP/.worktrees/atlas-api && python3 simple_main.py`
- [ ] Frontend running on `http://localhost:5174`
  - Start: `cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard && npm run dev`

### Required Software
- [ ] Node.js installed
- [ ] Playwright installed (`npm install -D @playwright/test`)
- [ ] Playwright browsers installed (`npx playwright install`)

**Check all at once**: Run `./tests/e2e/verify-setup.sh`

---

## Test File Details

### 01 - Navigation Tests (64 lines)
**Purpose**: Verify core navigation, routing, and UI consistency

**Tests**:
1. Homepage loads with correct title
2. Navigate to all 9 pages successfully
3. Sidebar is visible
4. Active route highlighting works
5. Responsive sidebar on mobile
6. Consistent header across pages

**Key Areas**: Page routing, sidebar, responsive design

---

### 02 - CSV Upload Tests (95 lines)
**Purpose**: Test file upload, quality analysis, and PII detection

**Tests**:
1. Upload CSV and display results
2. Show quality dimensions (completeness, uniqueness, validity)
3. Display PII detections with confidence
4. Show upload progress indicator
5. Handle empty files gracefully
6. Validate file format

**Key Areas**: File upload, quality metrics, PII detection, error handling

---

### 03 - Connector Tests (93 lines)
**Purpose**: Test data source connector management

**Tests**:
1. Display connectors page
2. Show available connector types
3. Open creation wizard
4. Create PostgreSQL connector
5. List existing connectors
6. Show connector details
7. Validate required fields

**Key Areas**: CRUD operations, form validation, wizard workflow

---

### 04 - Quality Reports Tests (66 lines)
**Purpose**: Test quality reports listing and filtering

**Tests**:
1. Display quality reports page
2. Show search and filters
3. Display reports list or empty state
4. Search functionality works
5. Show quality metrics in reports
6. Allow filtering by date range

**Key Areas**: Search, filters, data display

---

### 05 - GDPR Tests (77 lines)
**Purpose**: Test GDPR compliance workflows

**Tests**:
1. Display GDPR page
2. Show request form
3. Submit export request
4. Show request types (Export, Delete, Access)
5. Validate email format
6. Show request history

**Key Areas**: Request workflows, validation, compliance features

---

### 06 - Data Catalog Tests (71 lines)
**Purpose**: Test dataset catalog and metadata

**Tests**:
1. Display catalog page
2. Search functionality
3. Display datasets or empty state
4. Show dataset metadata
5. Allow filtering datasets
6. Navigate to dataset details

**Key Areas**: Catalog browsing, search, metadata display

---

### 07 - Feature Store Tests (68 lines)
**Purpose**: Test feature store operations

**Tests**:
1. Display feature store page
2. Show register button
3. Display features or empty state
4. Show feature metadata
5. Allow searching features
6. Open feature registration form

**Key Areas**: Feature management, registration workflow

---

### 08 - User Journey Tests (131 lines)
**Purpose**: Test complete end-to-end workflows

**Tests**:
1. Upload CSV → View Quality → Check PII
2. Create Connector → Test Connection
3. Dashboard → Upload → PII Report
4. Upload → GDPR Request
5. Full platform tour (all 9 pages)

**Key Areas**: Complete workflows, multi-page flows, integration

---

### 09 - Performance Tests (107 lines)
**Purpose**: Benchmark load times and performance

**Tests**:
1. Dashboard loads in <3 seconds
2. Page navigation in <1 second
3. Upload page renders in <2 seconds
4. No excessive console errors
5. Large CSV (1000 rows) processes in <30 seconds
6. API health check responds in <500ms

**Key Areas**: Load times, performance metrics, benchmarking

---

### 10 - Visual Tests (115 lines)
**Purpose**: Visual regression and responsive design

**Tests**:
1. Dashboard snapshot baseline
2. Upload page snapshot
3. Connectors page snapshot
4. Consistent header across pages
5. Responsive design on mobile (375x667)
6. Responsive design on tablet (768x1024)
7. Dark mode compatibility
8. Consistent styling across pages

**Key Areas**: Visual regression, responsive design, consistency

---

## Helpers & Utilities

### setup.ts (41 lines)
**Purpose**: Reusable test utilities

**Functions**:
- `waitForAPI()` - Wait for backend health check
- `createTestCSV(filename)` - Generate small test CSV (2 rows)
- `createLargeTestCSV(filename, rows)` - Generate large test CSV
- `cleanupTestFiles(...filenames)` - Delete temporary files

**Usage**:
```typescript
import { createTestCSV, cleanupTestFiles } from './helpers/setup';

const csvPath = await createTestCSV('test.csv');
// ... use in test
await cleanupTestFiles('test.csv');
```

---

## Configuration Files

### playwright.config.ts
**Settings**:
- Test directory: `./tests/e2e`
- Base URL: `http://localhost:5174`
- Browsers: Chromium, Firefox
- Parallel: Yes
- Retries: 2 in CI, 0 locally
- Screenshot: On failure
- Trace: On first retry
- Auto-start dev server: Yes

---

## Common Workflows

### First Time Setup
1. Install dependencies: `npm install`
2. Install Playwright: `npm install -D @playwright/test`
3. Install browsers: `npx playwright install`
4. Verify setup: `./tests/e2e/verify-setup.sh`
5. Run tests: `npm run test:e2e:ui`

### Running Tests Regularly
1. Start backend: `cd atlas-api && python3 simple_main.py`
2. Start frontend: `npm run dev` (in dashboard directory)
3. Run tests: `npm run test:e2e`
4. View report: `npm run test:e2e:report`

### Debugging Failed Tests
1. Run in debug mode: `npm run test:e2e:debug`
2. Or run with headed browser: `npm run test:e2e:headed`
3. Check screenshots in `test-results/`
4. Review HTML report: `npm run test:e2e:report`
5. Run specific test: `npx playwright test -g "test name"`

### Updating Visual Baselines
1. Make UI changes
2. Run tests: `npm run test:e2e`
3. Review failures in report
4. If intentional, update: `npx playwright test --update-snapshots`
5. Commit updated screenshots

---

## Documentation Deep Dive

### README.md (Comprehensive Guide)
**Sections**:
- Running Tests (all modes)
- Test Coverage (detailed breakdown)
- Prerequisites (setup guide)
- Test Helpers (utility functions)
- CI/CD Integration (GitHub Actions)
- Troubleshooting (common issues)
- Best Practices (testing guidelines)
- Contributing (adding new tests)

**Best For**: Complete reference, troubleshooting, contributing

### QUICK_START.md (Getting Started)
**Sections**:
- Prerequisites checklist
- Quick commands
- Test structure overview
- First-time setup
- Understanding results
- Common issues
- Running individual tests
- Debugging tests
- Performance benchmarks
- Visual regression

**Best For**: First-time users, quick reference

### TEST_SUMMARY.md (Statistics & Metrics)
**Sections**:
- Test suite statistics
- File breakdown
- Feature coverage matrix
- Test helpers
- Performance benchmarks
- Browser coverage
- Success criteria
- Execution time estimates
- CI/CD readiness
- Maintenance notes

**Best For**: Overview, metrics, planning

---

## Success Metrics

### Completed ✅
- ✅ 928 lines of test code
- ✅ 57 test cases
- ✅ 100% page coverage (9/9)
- ✅ Cross-browser (Chromium, Firefox)
- ✅ Performance benchmarks
- ✅ Visual regression
- ✅ Complete documentation
- ✅ Test utilities
- ✅ Verification scripts
- ✅ CI/CD ready

### Test Quality
- Proper wait strategies (no flaky timeouts)
- Helper functions for reusability
- Clear, descriptive test names
- Both success and error states tested
- Performance metrics included
- Visual regression baselines
- Comprehensive documentation

---

## Next Steps

1. **Run Your First Test**
   ```bash
   ./tests/e2e/verify-setup.sh
   npm run test:e2e:ui
   ```

2. **Review Results**
   - Check pass/fail status
   - Review screenshots
   - Check performance metrics

3. **Add New Tests**
   - Create new `.spec.ts` file
   - Follow existing patterns
   - Update documentation

4. **Maintain Baselines**
   - Update visual snapshots when UI changes
   - Keep test data relevant
   - Monitor performance trends

5. **Integrate with CI/CD**
   - Set up GitHub Actions
   - Configure test reports
   - Set up notifications

---

## Support & Resources

### Internal Documentation
- [README.md](README.md) - Full guide
- [QUICK_START.md](QUICK_START.md) - Quick reference
- [TEST_SUMMARY.md](TEST_SUMMARY.md) - Statistics

### Playwright Resources
- [Playwright Docs](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)

### Getting Help
- Run `./tests/e2e/verify-setup.sh` for diagnostics
- Check test reports: `npm run test:e2e:report`
- Review screenshots in `test-results/`
- Debug mode: `npm run test:e2e:debug`

---

**Status**: READY FOR USE ✅
**Last Updated**: 2026-01-09
**Test Suite Version**: 1.0.0
