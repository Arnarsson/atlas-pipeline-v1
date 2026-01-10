import { test, expect } from '@playwright/test';

test.describe('Feature Store', () => {
  test('should display feature store page', async ({ page }) => {
    await page.goto('/features');

    await expect(page.locator('h1, h2')).toContainText(/Feature|Features/i);
  });

  test('should show register button', async ({ page }) => {
    await page.goto('/features');

    await expect(page.locator('button:has-text("Register"), button:has-text("Upload"), button:has-text("Create"), button:has-text("Add")')).toBeVisible();
  });

  test('should display features or empty state', async ({ page }) => {
    await page.goto('/features');

    // Should show either features table or empty state
    const hasContent = await page.locator('table, text=/No features|No data/i').count() > 0;
    expect(hasContent).toBeTruthy();
  });

  test('should show feature metadata', async ({ page }) => {
    await page.goto('/features');

    // Look for feature-related terms
    const featureTerms = ['Name', 'Type', 'Dataset', 'Description', 'Version'];

    let foundTerm = false;
    for (const term of featureTerms) {
      if (await page.locator(`text=${term}`).isVisible()) {
        foundTerm = true;
        break;
      }
    }

    expect(foundTerm || await page.locator('text=/No features|No data/i').isVisible()).toBeTruthy();
  });

  test('should allow searching features', async ({ page }) => {
    await page.goto('/features');

    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i]');

    if (await searchInput.isVisible()) {
      await searchInput.fill('customer');
      await page.waitForTimeout(1000);
    }
  });

  test('should open feature registration form', async ({ page }) => {
    await page.goto('/features');

    // Click register/create button
    const registerButton = page.locator('button:has-text("Register"), button:has-text("Create"), button:has-text("Add")').first();
    await registerButton.click();

    // Should show form or modal
    await page.waitForTimeout(1000);

    // Look for form fields
    const formFields = page.locator('input[name], textarea, select');
    const hasForm = await formFields.count() > 0;
    expect(hasForm).toBeTruthy();
  });
});
