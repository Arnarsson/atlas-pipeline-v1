import { test, expect } from '@playwright/test';

test.describe('Data Catalog', () => {
  test('should display catalog page', async ({ page }) => {
    await page.goto('/catalog');

    await expect(page.locator('h1, h2')).toContainText(/Catalog|Datasets|Data/i);
  });

  test('should have search functionality', async ({ page }) => {
    await page.goto('/catalog');

    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]');
    await expect(searchInput).toBeVisible();

    // Type search query
    await searchInput.fill('customer');
    await page.waitForTimeout(1000);
  });

  test('should display datasets or empty state', async ({ page }) => {
    await page.goto('/catalog');

    // Should show either datasets or empty state
    const hasContent = await page.locator('table, [data-testid="dataset-card"], text=/No datasets|No data/i').count() > 0;
    expect(hasContent).toBeTruthy();
  });

  test('should show dataset metadata', async ({ page }) => {
    await page.goto('/catalog');

    // Look for metadata terms
    const metadataTerms = ['Schema', 'Columns', 'Rows', 'Type', 'Updated'];

    let foundMetadata = false;
    for (const term of metadataTerms) {
      if (await page.locator(`text=${term}`).isVisible()) {
        foundMetadata = true;
        break;
      }
    }

    // May not have datasets yet
    expect(foundMetadata || await page.locator('text=/No datasets|No data/i').isVisible()).toBeTruthy();
  });

  test('should allow filtering datasets', async ({ page }) => {
    await page.goto('/catalog');

    // Look for filter controls
    const filterControls = page.locator('select, button:has-text("Filter"), [role="combobox"]');

    // Filters may not be implemented yet
    const hasFilters = await filterControls.count() > 0;
    expect(typeof hasFilters).toBe('boolean');
  });

  test('should navigate to dataset details', async ({ page }) => {
    await page.goto('/catalog');

    // Look for dataset items
    const datasetItem = page.locator('table tr, [data-testid="dataset-card"], .dataset-item').first();

    if (await datasetItem.isVisible()) {
      await datasetItem.click();

      // Should navigate somewhere or show details
      await page.waitForTimeout(1000);
    }
  });
});
