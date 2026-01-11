import { test, expect } from '@playwright/test';
import { createTestCSV, cleanupTestFiles } from './helpers/setup';

test.describe('API Contract Validation', () => {
  let csvPath: string;

  test.beforeEach(async () => {
    csvPath = await createTestCSV('contract_test.csv');
  });

  test.afterEach(async () => {
    await cleanupTestFiles('contract_test.csv');
  });

  test('Quality Metrics API returns correct structure', async ({ page, request }) => {
    // Upload CSV
    await page.goto('/upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const datasetInput = page.locator('input#dataset-name');
    if (await datasetInput.isVisible()) {
      await datasetInput.fill('contract_test');
    }

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Wait for results
    await page.waitForSelector('[data-testid="quality-metrics-section"]', { timeout: 30000 });

    // Extract run ID from page
    const runInfo = page.locator('[data-testid="run-info"]');
    await expect(runInfo).toBeVisible();
    const runIdText = await runInfo.textContent();
    const runIdMatch = runIdText?.match(/Run ID:\s+([a-f0-9-]+)/);

    expect(runIdMatch).toBeTruthy();
    const runId = runIdMatch![1];

    // Call API directly to verify structure
    const response = await request.get(`http://localhost:8000/quality/metrics/${runId}`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();

    // Verify root properties
    expect(data).toHaveProperty('run_id');
    expect(data).toHaveProperty('overall_score');
    expect(data).toHaveProperty('dimensions');
    expect(data).toHaveProperty('column_metrics');

    // Verify dimensions structure - all 6 dimensions
    const expectedDimensions = ['completeness', 'uniqueness', 'validity', 'consistency', 'accuracy', 'timeliness'];
    for (const dim of expectedDimensions) {
      expect(data.dimensions).toHaveProperty(dim);
      expect(data.dimensions[dim]).toHaveProperty('score');
      expect(data.dimensions[dim]).toHaveProperty('threshold');
      expect(data.dimensions[dim]).toHaveProperty('passed');
      expect(data.dimensions[dim]).toHaveProperty('details');

      // Verify types
      expect(typeof data.dimensions[dim].score).toBe('number');
      expect(typeof data.dimensions[dim].threshold).toBe('number');
      expect(typeof data.dimensions[dim].passed).toBe('boolean');
    }

    // Verify column_metrics structure
    expect(typeof data.column_metrics).toBe('object');
    if (Object.keys(data.column_metrics).length > 0) {
      const firstColumn = Object.values(data.column_metrics)[0] as any;
      expect(firstColumn).toHaveProperty('completeness');
      expect(firstColumn).toHaveProperty('uniqueness');
      expect(firstColumn).toHaveProperty('validity');
      expect(firstColumn).toHaveProperty('data_type');
      expect(firstColumn).toHaveProperty('null_count');

      expect(typeof firstColumn.completeness).toBe('number');
      expect(typeof firstColumn.uniqueness).toBe('number');
      expect(typeof firstColumn.validity).toBe('number');
    }
  });

  test('PII Report API returns correct structure', async ({ page, request }) => {
    // Upload CSV
    await page.goto('/upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const datasetInput = page.locator('input#dataset-name');
    if (await datasetInput.isVisible()) {
      await datasetInput.fill('pii_contract_test');
    }

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Wait for results
    await page.waitForSelector('[data-testid="pii-results-section"]', { timeout: 30000 });

    // Extract run ID
    const runInfo = page.locator('[data-testid="run-info"]');
    await expect(runInfo).toBeVisible();
    const runIdText = await runInfo.textContent();
    const runIdMatch = runIdText?.match(/Run ID:\s+([a-f0-9-]+)/);

    expect(runIdMatch).toBeTruthy();
    const runId = runIdMatch![1];

    // Call API directly
    const response = await request.get(`http://localhost:8000/quality/pii-report/${runId}`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();

    // Verify root properties
    expect(data).toHaveProperty('run_id');
    expect(data).toHaveProperty('dataset_name');
    expect(data).toHaveProperty('total_detections');
    expect(data).toHaveProperty('detections_by_type');
    expect(data).toHaveProperty('detections');
    expect(data).toHaveProperty('compliance_status');
    expect(data).toHaveProperty('recommendations');

    // Verify types
    expect(typeof data.total_detections).toBe('number');
    expect(typeof data.detections_by_type).toBe('object');
    expect(Array.isArray(data.detections)).toBe(true);
    expect(['compliant', 'warning', 'violation']).toContain(data.compliance_status);
    expect(Array.isArray(data.recommendations)).toBe(true);

    // Verify detection structure if detections exist
    if (data.detections.length > 0) {
      const detection = data.detections[0];
      expect(detection).toHaveProperty('entity_type');
      expect(detection).toHaveProperty('location');
      expect(detection.location).toHaveProperty('row');
      expect(detection.location).toHaveProperty('column');
      expect(detection).toHaveProperty('confidence');
      expect(detection).toHaveProperty('matched_text');

      expect(typeof detection.confidence).toBe('number');
      expect(typeof detection.matched_text).toBe('string');
    }
  });

  test('Frontend displays all 6 quality dimensions', async ({ page }) => {
    await page.goto('/upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const datasetInput = page.locator('input#dataset-name');
    if (await datasetInput.isVisible()) {
      await datasetInput.fill('dimensions_test');
    }

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Wait for quality metrics
    await page.waitForSelector('[data-testid="quality-dimensions"]', { timeout: 30000 });

    const dimensions = page.locator('[data-testid="quality-dimensions"] > div');
    const count = await dimensions.count();

    // Should show all 6 dimensions
    expect(count).toBe(6);

    // Verify each dimension is visible
    const expectedDimensions = ['Completeness', 'Uniqueness', 'Validity', 'Consistency', 'Accuracy', 'Timeliness'];
    for (const dim of expectedDimensions) {
      await expect(page.getByText(dim)).toBeVisible();
    }
  });

  test('Frontend displays PII compliance status and recommendations', async ({ page }) => {
    await page.goto('/upload');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const datasetInput = page.locator('input#dataset-name');
    if (await datasetInput.isVisible()) {
      await datasetInput.fill('pii_compliance_test');
    }

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Wait for PII results
    await page.waitForSelector('[data-testid="pii-results-section"]', { timeout: 30000 });

    // Verify compliance status card exists
    const piiTable = page.locator('[data-testid="pii-table"]');
    await expect(piiTable).toBeVisible();

    // Should have summary section with compliance status
    const summary = page.locator('[data-testid="pii-summary"]');
    await expect(summary).toBeVisible();

    // Should show compliance status (compliant, warning, or violation)
    const complianceText = await piiTable.textContent();
    expect(
      complianceText?.toLowerCase().includes('compliant') ||
      complianceText?.toLowerCase().includes('warning') ||
      complianceText?.toLowerCase().includes('violation')
    ).toBeTruthy();
  });
});
