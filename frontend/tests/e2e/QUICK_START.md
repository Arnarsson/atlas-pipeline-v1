# E2E Tests - Quick Start Guide

## Prerequisites

1. **Backend API must be running**
   ```bash
   cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
   python3 simple_main.py
   # Should see: "Uvicorn running on http://127.0.0.1:8000"
   ```

2. **Frontend must be running**
   ```bash
   cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard
   npm run dev
   # Should see: "Local: http://localhost:5174/"
   ```

## Running Tests

### Quick Commands

```bash
# Run all tests
npm run test:e2e

# Interactive UI mode (recommended for first run)
npm run test:e2e:ui

# Debug mode (step through tests)
npm run test:e2e:debug

# View last test report
npm run test:e2e:report

# Run with visible browser
npm run test:e2e:headed

# Run only Chromium tests
npm run test:e2e:chromium

# Run only Firefox tests
npm run test:e2e:firefox
```

### Using Test Runner Script

```bash
./tests/e2e/run-tests.sh
```

This script:
- Checks if backend API is running
- Checks if frontend is running
- Runs all tests
- Shows report command at end

## Test Structure

```
tests/e2e/
├── 01-navigation.spec.ts      (6 tests)   - Page navigation, sidebar, routing
├── 02-csv-upload.spec.ts      (6 tests)   - File upload, quality, PII detection
├── 03-connectors.spec.ts      (7 tests)   - Connector CRUD operations
├── 04-quality-reports.spec.ts (6 tests)   - Reports list, search, filters
├── 05-gdpr.spec.ts            (6 tests)   - GDPR request workflows
├── 06-catalog.spec.ts         (6 tests)   - Data catalog, search, metadata
├── 07-features.spec.ts        (6 tests)   - Feature store operations
├── 08-user-journey.spec.ts    (5 tests)   - End-to-end user workflows
├── 09-performance.spec.ts     (6 tests)   - Load times, performance metrics
├── 10-visual.spec.ts          (8 tests)   - Visual regression, screenshots
└── helpers/
    └── setup.ts                           - Test utilities
```

## First Time Setup

1. **Install Playwright** (already done if you see `@playwright/test` in package.json)
   ```bash
   npm install -D @playwright/test
   npx playwright install
   ```

2. **Verify services are running**
   ```bash
   curl http://localhost:8000/health  # Should return 200
   curl http://localhost:5174         # Should return HTML
   ```

3. **Run tests in UI mode** (easiest to see what's happening)
   ```bash
   npm run test:e2e:ui
   ```

## Understanding Test Results

### Green checkmark ✓
Test passed successfully

### Red X ✗
Test failed - click to see:
- Error message
- Screenshot at failure point
- Execution trace

### Test Report
After tests complete, run:
```bash
npm run test:e2e:report
```

Opens HTML report showing:
- Pass/fail status per test
- Screenshots of failures
- Performance metrics
- Console logs

## Common Issues

### "Target closed" or "Browser disconnected"
- Frontend or backend crashed
- Check terminal for errors
- Restart services

### "Timeout exceeded"
- Page took too long to load
- Backend may be slow or not responding
- Check API is running: `curl http://localhost:8000/health`

### "Element not found"
- UI changed since test was written
- Check page structure matches test expectations
- May need to update selectors

### Visual regression failures
- Screenshot doesn't match baseline
- Run with `--update-snapshots` to accept new version:
  ```bash
  npx playwright test --update-snapshots
  ```

## Running Individual Tests

```bash
# Run specific test file
npx playwright test 02-csv-upload.spec.ts

# Run specific test by name
npx playwright test -g "should upload CSV"

# Run tests matching pattern
npx playwright test navigation

# Run in headed mode (see browser)
npx playwright test 02-csv-upload.spec.ts --headed

# Run with slow motion (1 second delay between actions)
npx playwright test --slow-mo=1000
```

## Debugging Tests

### Visual debugger (recommended)
```bash
npx playwright test --debug
```

Opens Playwright Inspector where you can:
- Step through test line by line
- See what element is being targeted
- View page state at each step
- Edit selectors and try them out

### Console output
```bash
npx playwright test --reporter=list
```

Shows detailed console output during test execution.

### Screenshots on failure
Already enabled by default. Find in:
```
test-results/
└── <test-name>/
    └── test-failed-1.png
```

## Performance Benchmarks

Tests verify:
- Dashboard loads in <3 seconds
- Page navigation in <1 second
- Upload page renders in <2 seconds
- API health check in <500ms
- Large CSV (1000 rows) processes in <30 seconds

If these fail, investigate:
- Backend performance
- Network latency
- Database query speed
- Frontend bundle size

## Visual Regression Tests

Baseline screenshots are stored in `tests/e2e/__screenshots__/`

When UI changes:
1. Review changes in HTML report
2. If expected, update baselines:
   ```bash
   npx playwright test --update-snapshots
   ```
3. Commit updated screenshots

## CI/CD Integration

For GitHub Actions, see `tests/e2e/README.md` for full example.

Key points:
- Use `npx playwright install --with-deps` to install browsers
- Start backend and frontend before tests
- Set `CI=true` environment variable
- Upload test reports as artifacts

## Next Steps

1. Run tests in UI mode to see them in action
2. Review HTML report to understand coverage
3. Add tests for new features as they're built
4. Keep baselines updated when UI changes
5. Monitor performance metrics over time
