import { Page, expect } from '@playwright/test';
import * as fs from 'fs';

export async function waitForAPI(page: Page) {
  // Wait for API to be healthy
  const response = await page.request.get('http://localhost:8000/health');
  expect(response.status()).toBe(200);
}

export async function createTestCSV(filename: string): Promise<string> {
  const csv = `customer_id,name,email,phone
C001,Test User,test@example.com,+4512345678
C002,Jane Doe,jane@test.com,+4587654321`;

  // Write to temp file
  const path = `/tmp/${filename}`;
  fs.writeFileSync(path, csv);
  return path;
}

export async function createLargeTestCSV(filename: string, rows: number = 100): Promise<string> {
  let csv = `customer_id,name,email,phone,address\n`;

  for (let i = 1; i <= rows; i++) {
    csv += `C${i.toString().padStart(3, '0')},User ${i},user${i}@example.com,+45${Math.floor(10000000 + Math.random() * 90000000)},Street ${i}\n`;
  }

  const path = `/tmp/${filename}`;
  fs.writeFileSync(path, csv);
  return path;
}

export async function cleanupTestFiles(...filenames: string[]) {
  for (const filename of filenames) {
    try {
      fs.unlinkSync(`/tmp/${filename}`);
    } catch (e) {
      // Ignore if file doesn't exist
    }
  }
}
