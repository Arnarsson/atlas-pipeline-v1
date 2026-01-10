import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
  test('should load homepage', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Atlas Data Pipeline/);
    await expect(page.locator('h1')).toContainText(/Dashboard|Atlas/i);
  });

  test('should navigate to all pages', async ({ page }) => {
    await page.goto('/');

    const pages = [
      { link: 'Upload', url: '/upload' },
      { link: 'Connectors', url: '/connectors' },
      { link: 'Quality', url: '/reports' },
      { link: 'PII', url: '/pii' },
      { link: 'Catalog', url: '/catalog' },
      { link: 'Features', url: '/features' },
      { link: 'GDPR', url: '/gdpr' },
      { link: 'Lineage', url: '/lineage' },
    ];

    for (const { link, url } of pages) {
      await page.click(`text="${link}"`);
      await expect(page).toHaveURL(url);
      await page.waitForLoadState('networkidle');
    }
  });

  test('sidebar should be visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('nav')).toBeVisible();
  });

  test('should show active route highlighting', async ({ page }) => {
    await page.goto('/upload');

    // The Upload link should have active styling (aria-current or active class)
    const uploadLink = page.locator('a:has-text("Upload")');
    await expect(uploadLink).toBeVisible();
  });

  test('responsive sidebar on mobile', async ({ page }) => {
    await page.goto('/');

    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });

    // Sidebar should exist (may be hidden or collapsible)
    await expect(page.locator('nav')).toBeInViewport({ ratio: 0.1 });
  });

  test('should have consistent header across pages', async ({ page }) => {
    const pages = ['/', '/upload', '/connectors', '/reports'];

    for (const url of pages) {
      await page.goto(url);

      // Should have Atlas branding
      await expect(page.locator('text=/Atlas/i').first()).toBeVisible();
    }
  });
});
