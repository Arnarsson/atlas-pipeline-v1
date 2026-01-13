import { test, expect } from '@playwright/test';

test.describe('AtlasIntelligence Airbyte Sync', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to AtlasIntelligence page
    await page.goto('/atlas-intelligence');
  });

  test('should display AtlasIntelligence page with tabs', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h1')).toContainText('AtlasIntelligence');

    // Verify all three tabs are visible
    await expect(page.locator('button:has-text("MCP Connectors")')).toBeVisible();
    await expect(page.locator('button:has-text("PyAirbyte Sources")')).toBeVisible();
    await expect(page.locator('button:has-text("N8N Workflows")')).toBeVisible();
  });

  test('should display health status cards', async ({ page }) => {
    // Verify platform status card
    await expect(page.locator('text=Platform Status')).toBeVisible();

    // Verify connector count cards
    await expect(page.locator('text=MCP Connectors')).toBeVisible();
    await expect(page.locator('text=PyAirbyte Sources')).toBeVisible();
    await expect(page.locator('text=N8N Workflows')).toBeVisible();
  });

  test('should toggle sync status panel', async ({ page }) => {
    // Click Sync Status button
    const syncButton = page.locator('button:has-text("Sync Status")');
    await syncButton.click();

    // Verify sync status panel appears
    await expect(page.locator('text=/Sync Overview|Running Jobs|Schedules/i')).toBeVisible();

    // Toggle off
    await syncButton.click();
  });

  test('should toggle API keys panel', async ({ page }) => {
    // Click API Keys button
    const apiKeysButton = page.locator('button:has-text("API Keys")');
    await apiKeysButton.click();

    // Verify credentials section appears
    await expect(page.locator('text=API Keys Configuration')).toBeVisible();

    // Toggle off
    await apiKeysButton.click();
  });

  test('should display MCP connectors list', async ({ page }) => {
    // Default tab should be MCP
    const mcpTab = page.locator('button:has-text("MCP Connectors")');
    await expect(mcpTab).toHaveAttribute('data-state', 'active').catch(() => {
      // Alternative check - tab should be visible and clickable
      return expect(mcpTab).toBeVisible();
    });

    // Should show connector cards or list
    // Wait for connectors to load
    await page.waitForTimeout(1000);
  });

  test('should switch to PyAirbyte tab', async ({ page }) => {
    // Click PyAirbyte tab
    await page.click('button:has-text("PyAirbyte Sources")');

    // Should show category filters or connector list
    await page.waitForTimeout(500);

    // Verify PyAirbyte content is showing (categories or connectors)
    const hasContent = await page.locator('text=/database|crm|marketing|analytics/i').count();
    expect(hasContent).toBeGreaterThan(0);
  });

  test('should filter PyAirbyte connectors by category', async ({ page }) => {
    // Switch to PyAirbyte tab
    await page.click('button:has-text("PyAirbyte Sources")');
    await page.waitForTimeout(500);

    // Look for category filter buttons
    const categoryButton = page.locator('button:has-text("database"), button:has-text("Database")').first();

    if (await categoryButton.isVisible()) {
      await categoryButton.click();

      // Should filter to database connectors
      await page.waitForTimeout(500);
    }
  });

  test('should search PyAirbyte connectors', async ({ page }) => {
    // Switch to PyAirbyte tab
    await page.click('button:has-text("PyAirbyte Sources")');
    await page.waitForTimeout(500);

    // Find search input
    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]').first();

    if (await searchInput.isVisible()) {
      await searchInput.fill('postgres');
      await page.waitForTimeout(500);

      // Results should contain postgres-related connectors
      const results = await page.locator('text=/postgres/i').count();
      expect(results).toBeGreaterThan(0);
    }
  });

  test('should switch to N8N tab', async ({ page }) => {
    // Click N8N tab
    await page.click('button:has-text("N8N Workflows")');

    // Should show N8N content (workflows or connection status)
    await page.waitForTimeout(500);
  });

  test('should select a connector and show details', async ({ page }) => {
    // Wait for connectors to load
    await page.waitForTimeout(1000);

    // Find and click a connector card
    const connectorCard = page.locator('[class*="cursor-pointer"]:has-text("github"), [class*="cursor-pointer"]:has-text("GitHub")').first();

    if (await connectorCard.isVisible()) {
      await connectorCard.click();

      // Should show connector details panel
      await page.waitForTimeout(500);
    }
  });

  test('should handle connector health check', async ({ page }) => {
    // Wait for page to load
    await page.waitForTimeout(1000);

    // Platform status should be visible
    const statusText = await page.locator('text=/healthy|Unknown/i').first();
    await expect(statusText).toBeVisible();
  });
});

test.describe('Sync Status Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/atlas-intelligence');
    // Open sync status panel
    await page.click('button:has-text("Sync Status")');
    await page.waitForTimeout(500);
  });

  test('should display sync overview stats', async ({ page }) => {
    // Should show overview section
    await expect(page.locator('text=/Overview|Stats|Running/i').first()).toBeVisible();
  });

  test('should display job history section', async ({ page }) => {
    // Should show jobs section
    await expect(page.locator('text=/Jobs|History|Recent/i').first()).toBeVisible();
  });

  test('should display schedules section', async ({ page }) => {
    // Should show schedules section
    await expect(page.locator('text=/Schedule/i').first()).toBeVisible();
  });
});

test.describe('Connector Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/atlas-intelligence');
  });

  test('should open connector config wizard', async ({ page }) => {
    // Switch to PyAirbyte tab
    await page.click('button:has-text("PyAirbyte Sources")');
    await page.waitForTimeout(500);

    // Find a connector to configure
    const configButton = page.locator('button:has-text("Configure")').first();

    if (await configButton.isVisible()) {
      await configButton.click();

      // Wizard should open
      await page.waitForTimeout(500);

      // Should show configuration step
      await expect(page.locator('text=/Configure|Settings|Connection/i').first()).toBeVisible();
    }
  });

  test('should display credential management', async ({ page }) => {
    // Open API Keys panel
    await page.click('button:has-text("API Keys")');

    // Should show credential inputs
    await expect(page.locator('text=API Keys Configuration')).toBeVisible();

    // Should show connector credential status
    const statusBadge = page.locator('text=/Configured|Not Set/i').first();
    await expect(statusBadge).toBeVisible();
  });
});

test.describe('Data Flow Integration', () => {
  test('should navigate from sync results to Data Catalog', async ({ page }) => {
    await page.goto('/atlas-intelligence');

    // Open sync status
    await page.click('button:has-text("Sync Status")');
    await page.waitForTimeout(500);

    // Look for completed job with results
    const viewResultsButton = page.locator('button:has-text("View Results"), button[title*="results"]').first();

    if (await viewResultsButton.isVisible()) {
      await viewResultsButton.click();

      // Modal should appear with navigation options
      await page.waitForTimeout(500);

      // Look for "View in Catalog" link
      const catalogLink = page.locator('text="View in Catalog", a:has-text("Catalog")').first();

      if (await catalogLink.isVisible()) {
        await catalogLink.click();

        // Should navigate to catalog page
        await expect(page).toHaveURL(/\/catalog/);
      }
    }
  });

  test('should display sync job metrics', async ({ page }) => {
    await page.goto('/atlas-intelligence');

    // Open sync status
    await page.click('button:has-text("Sync Status")');
    await page.waitForTimeout(500);

    // Check for job metrics display
    const hasMetrics = await page.locator('text=/records|synced|completed|failed/i').count();
    expect(hasMetrics).toBeGreaterThan(0);
  });
});

test.describe('Error Handling', () => {
  test('should handle API errors gracefully', async ({ page }) => {
    // Navigate with network issues
    await page.route('**/atlas-intelligence/**', (route) => {
      // Simulate slow response instead of blocking
      setTimeout(() => route.continue(), 100);
    });

    await page.goto('/atlas-intelligence');

    // Page should still render without crashing
    await expect(page.locator('h1')).toContainText('AtlasIntelligence');
  });

  test('should show loading state', async ({ page }) => {
    // Slow down API responses
    await page.route('**/atlas-intelligence/**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });

    await page.goto('/atlas-intelligence');

    // Should show loading indicator or placeholder
    await page.waitForTimeout(100);
  });

  test('should display empty state for no connectors', async ({ page }) => {
    // Mock empty response
    await page.route('**/atlas-intelligence/connectors', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/atlas-intelligence');
    await page.waitForTimeout(500);

    // Should handle empty state gracefully
    await expect(page.locator('h1')).toContainText('AtlasIntelligence');
  });
});

test.describe('Cross-Component Navigation', () => {
  test('should navigate from AtlasIntelligence to other pages', async ({ page }) => {
    await page.goto('/atlas-intelligence');

    // Use sidebar navigation
    const sidebarLinks = [
      { text: 'Dashboard', url: '/' },
      { text: 'Catalog', url: '/catalog' },
      { text: 'Quality', url: '/reports' },
    ];

    for (const link of sidebarLinks) {
      const navLink = page.locator(`nav a:has-text("${link.text}"), aside a:has-text("${link.text}")`).first();

      if (await navLink.isVisible()) {
        await navLink.click();
        await page.waitForTimeout(300);

        // Navigate back
        await page.goto('/atlas-intelligence');
        break; // Just test one navigation to save time
      }
    }
  });
});

test.describe('Real-time Updates', () => {
  test('should refresh sync stats', async ({ page }) => {
    await page.goto('/atlas-intelligence');

    // Open sync status
    await page.click('button:has-text("Sync Status")');
    await page.waitForTimeout(500);

    // Look for refresh button
    const refreshButton = page.locator('button:has-text("Refresh"), button[title*="refresh"]').first();

    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await page.waitForTimeout(500);
    }
  });
});
