import { test, expect } from '@playwright/test';

test.describe('No-Code Editor - Advanced Node Types and Indicators', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/strategy-hub/no-code-console');
  });

  test('should correctly render Ichimoku Cloud indicator with 5 outputs', async ({ page }) => {
    // 1. Find a technical indicator in the palette and drag it to the canvas
    const smaIndicator = page.locator('div[draggable]').filter({ hasText: 'Simple Moving Average' });
    const canvas = page.locator('.react-flow__pane');

    await smaIndicator.dragTo(canvas);

    // 2. Get the node that was just added and click it to open the properties panel
    const node = page.locator('.react-flow__node').first();
    await node.click();

    // Take a screenshot to debug
    await page.screenshot({ path: 'test-results/screenshot.png' });

    // 3. Wait for the properties panel to be visible by looking for the node's label in it
    const propertiesPanel = page.locator('div:has-text("Simple Moving Average") + div:has(select)');
    await expect(propertiesPanel).toBeVisible();

    const indicatorDropdown = propertiesPanel.locator('select');
    await indicatorDropdown.selectOption({ label: 'Ichimoku Cloud' });

    // 4. Verify the number of output handles
    const outputHandles = node.locator('.react-flow__handle-right');
    await expect(outputHandles).toHaveCount(5);

    // 5. Verify the labels of the output handles
    await expect(page.getByText('Tenkan')).toBeVisible();
    await expect(page.getByText('Kijun')).toBeVisible();
    await expect(page.getByText('Senkou A')).toBeVisible();
    await expect(page.getByText('Senkou B')).toBeVisible();
    await expect(page.getByText('Chikou')).toBeVisible();
  });
});
