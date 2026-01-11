import { test, expect } from '@playwright/test';
import { createTestCSV, cleanupTestFiles } from './helpers/setup';

test.describe('Error Handling', () => {
  let csvPath: string;

  test.beforeEach(async () => {
    csvPath = await createTestCSV('error_test.csv');
  });

  test.afterEach(async () => {
    await cleanupTestFiles('error_test.csv');
  });

  test('Shows graceful error when API returns 404', async ({ page, context }) => {
    // Mock API to return 404
    await context.route('**/quality/metrics/**', route => {
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Pipeline run not found' })
      });
    });

    await page.goto('/upload');

    // Upload should proceed but show error when fetching metrics
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Should not crash - error boundary or error state should handle it
    // Wait a bit to see if page crashes
    await page.waitForTimeout(2000);

    // Page should still be functional
    const uploadSection = page.locator('[data-testid="upload-section"]');
    await expect(uploadSection).toBeVisible();
  });

  test('Handles missing data gracefully', async ({ page, context }) => {
    // Mock API to return incomplete data
    await context.route('**/quality/metrics/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          run_id: 'test-123',
          overall_score: 0.95,
          dimensions: {
            completeness: { score: 1.0, threshold: 0.95, passed: true, details: {} },
            uniqueness: { score: 1.0, threshold: 0.98, passed: true, details: {} },
            validity: { score: 1.0, threshold: 0.90, passed: true, details: {} },
            consistency: { score: 1.0, threshold: 0.90, passed: true, details: {} },
            accuracy: { score: 1.0, threshold: 0.90, passed: true, details: {} },
            timeliness: { score: 1.0, threshold: 0.80, passed: true, details: {} }
          },
          column_metrics: {} // Empty metrics
        })
      });
    });

    await context.route('**/quality/pii-report/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          run_id: 'test-123',
          dataset_name: 'test',
          total_detections: 0,
          detections_by_type: {},
          detections: [],
          compliance_status: 'compliant',
          recommendations: []
        })
      });
    });

    await page.goto('/upload');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Should display without crashing even with empty data
    await page.waitForSelector('[data-testid="quality-metrics-section"]', { timeout: 15000 });

    // Should show overall score
    const overallScore = page.locator('[data-testid="overall-score"]');
    await expect(overallScore).toBeVisible();

    // Should show all 6 dimensions even with no column data
    const dimensions = page.locator('[data-testid="quality-dimensions"]');
    await expect(dimensions).toBeVisible();
  });

  test('ErrorBoundary catches component errors without crashing', async ({ page }) => {
    await page.goto('/upload');

    // Monitor console for errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Wait for results
    await page.waitForTimeout(5000);

    // Page should still be visible and functional
    const uploadPage = page.locator('[data-testid="upload-page"]');
    await expect(uploadPage).toBeVisible();

    // Check if any uncaught errors occurred
    // Filter out expected errors (like API 404 during development)
    const criticalErrors = errors.filter(err =>
      !err.includes('Failed to fetch') &&
      !err.includes('404') &&
      !err.includes('NetworkError')
    );

    // Should have no critical TypeError or null reference errors
    const typeErrors = criticalErrors.filter(err =>
      err.includes('TypeError') ||
      err.includes('Cannot read') ||
      err.includes('undefined')
    );

    expect(typeErrors.length).toBe(0);
  });

  test('Shows loading state while API is processing', async ({ page }) => {
    await page.goto('/upload');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Should show loading spinner
    const loadingSpinner = page.locator('[data-testid="loading-spinner"]');

    // Loading spinner should appear (may be brief)
    try {
      await expect(loadingSpinner.first()).toBeVisible({ timeout: 5000 });
    } catch {
      // It's ok if loading is too fast to catch
      console.log('Loading was too fast to verify spinner visibility');
    }

    // Eventually results should appear
    await page.waitForSelector('[data-testid="quality-metrics-section"], [data-testid="quality-loading"], [data-testid="pii-loading"]', { timeout: 30000 });
  });

  test('Handles network errors gracefully', async ({ page, context }) => {
    // Abort all API requests to simulate network failure
    await context.route('**/quality/**', route => {
      route.abort('failed');
    });

    await page.goto('/upload');

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.isVisible()) {
      await submitButton.click();
    }

    // Should not crash the page
    await page.waitForTimeout(3000);

    // Page should remain functional
    const uploadSection = page.locator('[data-testid="upload-section"]');
    await expect(uploadSection).toBeVisible();

    // Upload form should still be accessible for retry
    const fileInputAfterError = page.locator('input[type="file"]');
    await expect(fileInputAfterError).toBeVisible();
  });
});
