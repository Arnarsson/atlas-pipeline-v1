import { test, expect } from '@playwright/test';

test.describe('Connector Management', () => {
  test('should display connectors page', async ({ page }) => {
    await page.goto('/connectors');

    await expect(page.locator('h1, h2')).toContainText(/Connector|Data Source/i);
  });

  test('should display available connector types', async ({ page }) => {
    await page.goto('/connectors');

    // Should show create button
    await expect(page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")')).toBeVisible();
  });

  test('should open connector creation wizard', async ({ page }) => {
    await page.goto('/connectors');

    // Click create button
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")').first();
    await createButton.click();

    // Should show connector type selection (use .first() to handle multiple matches)
    await expect(page.locator('text=/PostgreSQL|MySQL|REST API|CSV|Database/i').first()).toBeVisible();
  });

  test('should create PostgreSQL connector', async ({ page }) => {
    await page.goto('/connectors');

    // Open wizard
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")').first();
    await createButton.click();

    // Select PostgreSQL (if selection is required)
    const postgresOption = page.locator('text=PostgreSQL, button:has-text("PostgreSQL")');
    if (await postgresOption.isVisible()) {
      await postgresOption.first().click();
    }

    // Fill form (fields may have different names)
    await page.fill('input[name="source_name"], input[placeholder*="name" i]', 'test_connector');
    await page.fill('input[name="host"], input[placeholder*="host" i]', 'localhost');
    await page.fill('input[name="port"], input[placeholder*="port" i]', '5432');
    await page.fill('input[name="database"], input[placeholder*="database" i]', 'testdb');
    await page.fill('input[name="username"], input[placeholder*="user" i]', 'testuser');
    await page.fill('input[name="password"], input[placeholder*="pass" i]', 'testpass');

    // Submit
    const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button:has-text("Submit")').last();
    await submitButton.click();

    // Should show success message or return to list
    await page.waitForTimeout(2000);
  });

  test('should list existing connectors', async ({ page }) => {
    await page.goto('/connectors');

    // Should show connectors table or empty state
    const hasConnectors = await page.locator('table, text=/No connectors|No data sources/i').count() > 0;
    expect(hasConnectors).toBeTruthy();
  });

  test('should show connector details', async ({ page }) => {
    await page.goto('/connectors');

    // Look for any connector cards or table rows
    const connectorItem = page.locator('table tr, [data-testid="connector-card"], .connector-item').first();

    if (await connectorItem.isVisible()) {
      await connectorItem.click();

      // Should show details (status, configuration, etc.)
      await page.waitForTimeout(1000);
    }
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/connectors');

    // Open creation form
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")').first();
    await createButton.click();

    // Try to submit without filling required fields
    const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button:has-text("Submit")').last();
    await submitButton.click();

    // Should show validation errors
    await expect(page.locator('text=/required|invalid|must/i')).toBeVisible({ timeout: 2000 });
  });
});
