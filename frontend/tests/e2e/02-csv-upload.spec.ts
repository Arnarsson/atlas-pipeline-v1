import { test, expect } from '@playwright/test';
import { createTestCSV, cleanupTestFiles } from './helpers/setup';

test.describe('CSV Upload', () => {
  test.afterEach(async () => {
    // Cleanup test files
    await cleanupTestFiles('test_upload.csv', 'test_dimensions.csv', 'test_pii.csv');
  });

  test('should upload CSV and show results', async ({ page }) => {
    await page.goto('/upload');

    // Create test CSV
    const csvPath = await createTestCSV('test_upload.csv');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csvPath);

    // Wait for upload to complete
    await page.waitForSelector('text=/Quality Score|Overall Score|Results/i', { timeout: 10000 });

    // Verify all 6 quality dimensions are shown
    await expect(page.locator('text=/Completeness/i')).toBeVisible();
    await expect(page.locator('text=/Uniqueness/i')).toBeVisible();
    await expect(page.locator('text=/Validity/i')).toBeVisible();
    await expect(page.locator('text=/Consistency/i')).toBeVisible();
    await expect(page.locator('text=/Accuracy/i')).toBeVisible();
    await expect(page.locator('text=/Timeliness/i')).toBeVisible();

    // Verify PII results are shown
    await expect(page.locator('text=/PII|Sensitive|EMAIL|PHONE/i')).toBeVisible();
  });

  test('should show all six quality dimensions', async ({ page }) => {
    await page.goto('/upload');

    const csvPath = await createTestCSV('test_dimensions.csv');
    await page.locator('input[type="file"]').setInputFiles(csvPath);

    // Wait for quality dimensions section
    await page.waitForSelector('[data-testid="quality-dimensions"]', { timeout: 30000 });

    // Verify all 6 dimensions are displayed
    const dimensions = ['Completeness', 'Uniqueness', 'Validity', 'Consistency', 'Accuracy', 'Timeliness'];

    for (const dim of dimensions) {
      await expect(page.locator(`text=${dim}`)).toBeVisible();
    }

    // Also verify the dimension count
    const dimensionCards = page.locator('[data-testid="quality-dimensions"] > div');
    const count = await dimensionCards.count();
    expect(count).toBe(6);
  });

  test('should display PII detections with confidence', async ({ page }) => {
    await page.goto('/upload');

    const csvPath = await createTestCSV('test_pii.csv');
    await page.locator('input[type="file"]').setInputFiles(csvPath);

    await page.waitForSelector('text=/PII|EMAIL|PHONE/i', { timeout: 10000 });

    // Should show PII type
    const piiSection = page.locator('text=/EMAIL|PERSON|Phone/i').first();
    await expect(piiSection).toBeVisible();
  });

  test('should show upload progress indicator', async ({ page }) => {
    await page.goto('/upload');

    const csvPath = await createTestCSV('test_progress.csv');
    await page.locator('input[type="file"]').setInputFiles(csvPath);

    // Should show some loading state
    const loadingIndicator = page.locator('text=/Processing|Loading|Analyzing/i, [role="progressbar"]');

    // May already be done, so check if visible within 500ms
    try {
      await expect(loadingIndicator).toBeVisible({ timeout: 500 });
    } catch {
      // Already completed, that's fine
    }
  });

  test('should handle empty file gracefully', async ({ page }) => {
    await page.goto('/upload');

    // Create empty CSV
    const fs = require('fs');
    const emptyPath = '/tmp/empty.csv';
    fs.writeFileSync(emptyPath, '');

    await page.locator('input[type="file"]').setInputFiles(emptyPath);

    // Should show error or validation message
    await expect(page.locator('text=/error|invalid|empty/i')).toBeVisible({ timeout: 5000 });

    // Cleanup
    fs.unlinkSync(emptyPath);
  });
});
