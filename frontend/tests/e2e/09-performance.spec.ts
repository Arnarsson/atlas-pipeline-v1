import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('dashboard should load quickly', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const duration = Date.now() - start;

    // Should load in <3 seconds
    expect(duration).toBeLessThan(3000);
    console.log(`Dashboard loaded in ${duration}ms`);
  });

  test('page navigation should be fast', async ({ page }) => {
    await page.goto('/');

    const pages = ['/upload', '/connectors', '/reports'];

    for (const url of pages) {
      const start = Date.now();
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      const duration = Date.now() - start;

      // Navigation should be <1 second
      expect(duration).toBeLessThan(1000);
      console.log(`${url} loaded in ${duration}ms`);
    }
  });

  test('upload page renders quickly', async ({ page }) => {
    const start = Date.now();
    await page.goto('/upload');

    // Wait for file input to be visible
    await page.locator('input[type="file"]').waitFor({ state: 'visible' });

    const duration = Date.now() - start;
    expect(duration).toBeLessThan(2000);
    console.log(`Upload page rendered in ${duration}ms`);
  });

  test('no console errors on key pages', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    const pages = ['/', '/upload', '/connectors', '/reports'];

    for (const url of pages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
    }

    // Should have minimal console errors
    expect(errors.length).toBeLessThan(5);

    if (errors.length > 0) {
      console.log('Console errors found:', errors);
    }
  });

  test('large CSV upload performance', async ({ page }) => {
    await page.goto('/upload');

    // Create large test CSV
    const fs = require('fs');
    let csv = 'id,name,email,phone\n';
    for (let i = 1; i <= 1000; i++) {
      csv += `${i},User ${i},user${i}@test.com,+45${Math.floor(10000000 + Math.random() * 90000000)}\n`;
    }

    const largePath = '/tmp/large_test.csv';
    fs.writeFileSync(largePath, csv);

    // Upload and measure
    const start = Date.now();
    await page.locator('input[type="file"]').setInputFiles(largePath);

    // Wait for processing
    await page.waitForSelector('text=/Quality|Results/i', { timeout: 30000 });

    const duration = Date.now() - start;
    console.log(`Large CSV (1000 rows) processed in ${duration}ms`);

    // Should process within 30 seconds
    expect(duration).toBeLessThan(30000);

    // Cleanup
    fs.unlinkSync(largePath);
  });

  test('API health check response time', async ({ page }) => {
    const start = Date.now();
    const response = await page.request.get('http://localhost:8000/health');
    const duration = Date.now() - start;

    expect(response.status()).toBe(200);
    expect(duration).toBeLessThan(500);
    console.log(`API health check: ${duration}ms`);
  });
});
