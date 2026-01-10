import { test, expect } from '@playwright/test';

test.describe('Visual Tests', () => {
  test('dashboard should match snapshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await expect(page).toHaveScreenshot('dashboard.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('upload page should match snapshot', async ({ page }) => {
    await page.goto('/upload');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('upload.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('connectors page should match snapshot', async ({ page }) => {
    await page.goto('/connectors');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('connectors.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('all pages should have consistent header', async ({ page }) => {
    const pages = ['/', '/upload', '/connectors', '/reports'];

    for (const url of pages) {
      await page.goto(url);

      // Should have Atlas branding
      await expect(page.locator('text=/Atlas/i').first()).toBeVisible();
    }
  });

  test('responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    const pages = ['/', '/upload', '/connectors'];

    for (const url of pages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');

      // Page should be visible and not overflow
      const body = page.locator('body');
      await expect(body).toBeVisible();

      // Take mobile screenshot
      const pageName = url === '/' ? 'dashboard' : url.substring(1);
      await expect(page).toHaveScreenshot(`${pageName}-mobile.png`, {
        fullPage: true,
        animations: 'disabled',
      });
    }
  });

  test('responsive design on tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard-tablet.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('dark mode compatibility', async ({ page }) => {
    await page.goto('/');

    // Check if dark mode toggle exists
    const darkModeToggle = page.locator('button[aria-label*="dark" i], button:has-text("Dark"), button:has-text("Theme")');

    if (await darkModeToggle.isVisible()) {
      // Click to enable dark mode
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      // Take dark mode screenshot
      await expect(page).toHaveScreenshot('dashboard-dark.png', {
        fullPage: true,
        animations: 'disabled',
      });
    }
  });

  test('consistent styling across pages', async ({ page }) => {
    const pages = ['/', '/upload', '/connectors', '/reports'];

    for (const url of pages) {
      await page.goto(url);

      // Check for consistent elements
      await expect(page.locator('nav')).toBeVisible(); // Sidebar

      // Header should exist
      const header = page.locator('header, h1, h2').first();
      await expect(header).toBeVisible();
    }
  });
});
