# Atlas Dashboard E2E Tests

Comprehensive Playwright E2E test suite covering all 9 pages and critical user workflows.

## Running Tests

### All tests
```bash
npm run test:e2e
```

### Interactive UI mode
```bash
npm run test:e2e:ui
```

### Debug mode
```bash
npm run test:e2e:debug
```

### Specific test file
```bash
npx playwright test tests/e2e/02-csv-upload.spec.ts
```

### Specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
```

### Using the test runner script
```bash
./tests/e2e/run-tests.sh
```

## Test Coverage

### 01 - Navigation (6 tests)
- Homepage loading
- Navigate to all 9 pages
- Sidebar visibility
- Active route highlighting
- Responsive sidebar
- Consistent header

### 02 - CSV Upload (6 tests)
- Upload CSV and show results
- Quality dimensions display
- PII detection with confidence
- Upload progress indicator
- Empty file handling
- Error states

### 03 - Connectors (7 tests)
- Display connectors page
- Available connector types
- Creation wizard
- PostgreSQL connector creation
- List existing connectors
- Connector details
- Field validation

### 04 - Quality Reports (6 tests)
- Display reports page
- Search and filters
- Reports list or empty state
- Search functionality
- Quality metrics display
- Date range filtering

### 05 - GDPR (6 tests)
- Display GDPR page
- Request form
- Export request submission
- Request types
- Email validation
- Request history

### 06 - Data Catalog (6 tests)
- Display catalog page
- Search functionality
- Datasets display
- Dataset metadata
- Filtering datasets
- Dataset details navigation

### 07 - Feature Store (6 tests)
- Display feature store page
- Register button
- Features display
- Feature metadata
- Search features
- Registration form

### 08 - User Journey (5 tests)
- End-to-end: Upload CSV → Quality → PII
- End-to-end: Create Connector → Test
- End-to-end: Dashboard → Upload → PII Report
- End-to-end: Upload → GDPR Request
- Full platform tour

### 09 - Performance (6 tests)
- Dashboard load time (<3s)
- Page navigation speed (<1s)
- Upload page render time (<2s)
- No console errors
- Large CSV upload (1000 rows, <30s)
- API health check (<500ms)

### 10 - Visual (8 tests)
- Dashboard snapshot
- Upload page snapshot
- Connectors page snapshot
- Consistent header
- Mobile responsive design
- Tablet responsive design
- Dark mode compatibility
- Consistent styling

## Total Test Coverage

- **10 test suites**
- **57 individual tests**
- **All 9 pages covered**
- **Cross-browser (Chromium, Firefox)**
- **Performance benchmarks**
- **Visual regression**

## Prerequisites

- Backend API running on http://localhost:8000
- Frontend running on http://localhost:5174
- PostgreSQL database running

## Starting Services

### Backend API
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-api
python3 simple_main.py
```

### Frontend
```bash
cd /Users/sven/Desktop/MCP/.worktrees/atlas-dashboard
npm run dev
```

## Test Helpers

### Creating Test CSV Files
```typescript
import { createTestCSV, createLargeTestCSV } from './helpers/setup';

// Small test file (2 rows)
const path = await createTestCSV('test.csv');

// Large test file (100 rows)
const largePath = await createLargeTestCSV('large.csv', 100);
```

### Cleanup Test Files
```typescript
import { cleanupTestFiles } from './helpers/setup';

test.afterEach(async () => {
  await cleanupTestFiles('test1.csv', 'test2.csv');
});
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Start Backend API
  run: |
    cd atlas-api
    python3 simple_main.py &
    sleep 5

- name: Start Frontend
  run: |
    npm run dev &
    sleep 5

- name: Run E2E tests
  run: npm run test:e2e

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Test Reports

After running tests, view the HTML report:
```bash
npx playwright show-report
```

Reports include:
- Test results by browser
- Screenshots on failure
- Execution traces
- Performance metrics
- Visual diffs

## Debugging Tests

### Visual debugger
```bash
npx playwright test --debug
```

### Headed mode (see browser)
```bash
npx playwright test --headed
```

### Slow motion
```bash
npx playwright test --slow-mo=1000
```

### Single test
```bash
npx playwright test -g "should upload CSV"
```

## Test Configuration

Configuration in `playwright.config.ts`:
- Base URL: http://localhost:5174
- Retry: 2x in CI, 0 in local
- Screenshot: only on failure
- Trace: on first retry
- Browsers: Chromium, Firefox
- Auto-start dev server

## Best Practices

1. **Use proper wait strategies**
   - `waitForSelector` for elements
   - `waitForLoadState('networkidle')` for pages
   - Avoid `waitForTimeout` except for visual states

2. **Create test data programmatically**
   - Use helper functions
   - Don't rely on existing data

3. **Clean up after tests**
   - Delete temporary files
   - Reset state when possible

4. **Handle both success and error states**
   - Test happy paths
   - Test validation errors
   - Test edge cases

5. **Use descriptive test names**
   - Should read like documentation
   - Explain expected behavior

6. **Keep tests independent**
   - Each test should run standalone
   - No dependencies between tests

## Troubleshooting

### Tests failing due to timeouts
- Increase timeout in test: `{ timeout: 30000 }`
- Check if services are running
- Check network speed

### Visual regression failures
- Update snapshots: `npx playwright test --update-snapshots`
- Review diffs in HTML report
- Ensure consistent environment

### Flaky tests
- Add proper wait conditions
- Check for race conditions
- Use `waitForLoadState` instead of fixed timeouts

### Browser not found
```bash
npx playwright install
```

## Contributing

When adding new tests:
1. Follow naming convention: `NN-feature.spec.ts`
2. Add to appropriate test suite or create new one
3. Update this README with test count
4. Ensure tests pass in both Chromium and Firefox
5. Add performance benchmarks where relevant
6. Include visual regression tests for UI changes
