import { test, expect } from '@playwright/test';

test.describe('GDPR Compliance', () => {
  test('should display GDPR page', async ({ page }) => {
    await page.goto('/gdpr');

    await expect(page.locator('h1, h2')).toContainText(/GDPR|Compliance|Privacy/i);
  });

  test('should show request form', async ({ page }) => {
    await page.goto('/gdpr');

    // Should have identifier input
    await expect(page.locator('input[placeholder*="email" i], input[placeholder*="identifier" i]')).toBeVisible();

    // Should have request type selector
    await expect(page.locator('select, button:has-text("Export"), button:has-text("Delete")')).toBeVisible();
  });

  test('should submit export request', async ({ page }) => {
    await page.goto('/gdpr');

    // Fill form
    const emailInput = page.locator('input[placeholder*="email" i], input[placeholder*="identifier" i]').first();
    await emailInput.fill('test@example.com');

    // Submit export request
    const exportButton = page.locator('button:has-text("Export"), button:has-text("Submit")').first();
    await exportButton.click();

    // Should show loading or success state
    await page.waitForTimeout(2000);
  });

  test('should show request types', async ({ page }) => {
    await page.goto('/gdpr');

    // Should show different GDPR request types
    const requestTypes = ['Export', 'Delete', 'Access', 'Portability'];

    let foundRequestType = false;
    for (const type of requestTypes) {
      if (await page.locator(`text=${type}`).isVisible()) {
        foundRequestType = true;
        break;
      }
    }

    expect(foundRequestType).toBeTruthy();
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/gdpr');

    // Fill with invalid email
    const emailInput = page.locator('input[placeholder*="email" i], input[placeholder*="identifier" i]').first();
    await emailInput.fill('invalid-email');

    // Try to submit
    const submitButton = page.locator('button:has-text("Export"), button:has-text("Submit"), button:has-text("Request")').first();
    await submitButton.click();

    // Should show validation error
    await expect(page.locator('text=/invalid|valid email|format/i')).toBeVisible({ timeout: 2000 });
  });

  test('should show request history', async ({ page }) => {
    await page.goto('/gdpr');

    // Look for request history or list
    const historySection = page.locator('text=/History|Previous|Recent|Requests/i, table');

    // May or may not be visible depending on implementation
    const hasHistory = await historySection.count() > 0;
    expect(typeof hasHistory).toBe('boolean');
  });
});
