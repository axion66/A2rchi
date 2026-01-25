import { test, expect } from '@playwright/test';

test.describe('Chat UI', () => {
  test('shows pipeline default model label', async ({ page }) => {
    await page.goto('/chat');
    const label = page.locator('#active-model-label');
    await expect(label).toContainText('Using pipeline default');
  });

  test('send button toggles to stop while streaming', async ({ page }) => {
    await page.goto('/chat');

    await page.route('**/api/get_chat_response_stream', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const body = '{"type":"chunk","content":"Hi"}\n';
      await route.fulfill({ status: 200, contentType: 'text/plain', body });
    });

    await page.getByLabel('Message input').fill('Hello');
    await page.getByRole('button', { name: 'Send message' }).click();

    await expect(page.getByRole('button', { name: 'Stop streaming' })).toBeVisible();
    await page.getByRole('button', { name: 'Stop streaming' }).click();
    await expect(page.getByRole('button', { name: 'Send message' })).toBeVisible();
  });

  test('A/B streaming includes provider overrides', async ({ page }) => {
    await page.goto('/chat');

    // Enable A/B testing
    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.locator('.settings-panel')).toBeVisible();
    await page.locator('.settings-nav-item[data-section="advanced"]').click();
    await expect(page.locator('#settings-advanced')).toBeVisible();
    await page.evaluate(() => {
      sessionStorage.setItem('a2rchi_ab_warning_dismissed', 'true');
    });
    await page.evaluate(() => {
      const checkbox = document.querySelector('#ab-checkbox');
      if (checkbox && checkbox instanceof HTMLInputElement) {
        checkbox.checked = true;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    // Switch back to Models section to configure providers
    await page.locator('.settings-nav-item[data-section="models"]').click();
    await expect(page.locator('#settings-models')).toBeVisible();

    // Select OpenRouter and custom model
    await page.locator('#provider-select').selectOption('openrouter');
    await page.locator('#model-select-primary').selectOption('__custom__');
    await page.locator('#custom-model-input').fill('openai/gpt-5-nano');

    // Configure provider B to OpenRouter and custom model too
    await page.evaluate(() => {
      const group = document.querySelector('.ab-model-group');
      if (group) {
        (group as HTMLElement).style.display = 'block';
      }
      const providerB = document.querySelector('#provider-select-b') as HTMLSelectElement | null;
      const modelB = document.querySelector('#model-select-b') as HTMLSelectElement | null;
      if (providerB) {
        providerB.value = 'openrouter';
        providerB.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (modelB) {
        modelB.value = '__custom__';
        modelB.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    await page.getByRole('button', { name: 'Close settings' }).click();

    const seen: Array<{ provider?: string; model?: string }> = [];
    await page.route('**/api/get_chat_response_stream', async (route) => {
      const postData = route.request().postData() || '';
      try {
        const payload = JSON.parse(postData);
        seen.push({ provider: payload.provider, model: payload.model });
      } catch {
        // ignore
      }
      const body = '{"type":"final","response":"OK","message_id":1,"user_message_id":1,"conversation_id":1}\n';
      await route.fulfill({ status: 200, contentType: 'text/plain', body });
    });

    await page.route('**/api/ab/create', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ comparison_id: 1 }),
      });
    });

    await page.getByLabel('Message input').fill('Test A/B');
    await page.getByRole('button', { name: 'Send message' }).click();

    await expect.poll(() => seen.length).toBeGreaterThan(1);
    const providers = seen.map((s) => s.provider);
    const models = seen.map((s) => s.model);
    expect(providers).toContain('openrouter');
    expect(models).toContain('openai/gpt-5-nano');
  });
});
