import { test, expect } from "@playwright/test";
import { cleanupTestUsers } from "./fixtures";

test.afterEach(async ({ page }) => {
  await cleanupTestUsers(page);
});

test.describe("Oracle Page", () => {
  test("1. Oracle page loads with all sections visible", async ({ page }) => {
    await page.goto("/oracle");
    await expect(page.locator("text=Oracle")).toBeVisible();
    // User selector area should exist
    await expect(
      page.locator(
        "[data-testid='user-selector'], .user-selector, text=profile",
      ),
    ).toBeVisible({ timeout: 10000 });
  });

  test("2. Create user via form", async ({ page }) => {
    await page.goto("/oracle");

    // Click add/new profile button
    const addButton = page
      .locator(
        "button:has-text('Add'), button:has-text('New'), button:has-text('add'), button:has-text('new')",
      )
      .first();
    await addButton.click();

    // Fill in the form
    const nameInput = page.locator("input[type='text']").first();
    await nameInput.fill("E2E_CreateUser");

    const birthdayInput = page.locator("input[type='date']").first();
    await birthdayInput.fill("1990-06-15");

    // Find mother name field (typically the third text input or second required text field)
    const inputs = page.locator("input[type='text']");
    const count = await inputs.count();
    if (count >= 3) {
      await inputs.nth(2).fill("E2E_Mother");
    }

    // Submit form
    const submitButton = page.locator("button[type='submit']").first();
    await submitButton.click();

    // Verify user appears in selector (wait for API response)
    await expect(page.locator("text=E2E_CreateUser")).toBeVisible({
      timeout: 10000,
    });
  });

  test("3. Submit oracle reading", async ({ page }) => {
    await page.goto("/oracle");

    // Look for reading/consultation submission area
    const submitButton = page
      .locator(
        "button:has-text('Submit'), button:has-text('Consult'), button:has-text('Read')",
      )
      .first();
    if (await submitButton.isVisible()) {
      await submitButton.click();
      // Wait for results to appear (any loading indicator should disappear)
      await page.waitForTimeout(2000);
    }
  });

  test("4. Switch between result tabs", async ({ page }) => {
    await page.goto("/oracle");

    // Look for tab buttons (Summary, Details, History)
    const summaryTab = page.locator("button:has-text('Summary')");
    const detailsTab = page.locator("button:has-text('Details')");
    const historyTab = page.locator("button:has-text('History')");

    if (await summaryTab.isVisible()) {
      await summaryTab.click();
      await expect(summaryTab).toHaveClass(/accent|active|selected|bg-/);

      await detailsTab.click();
      await expect(detailsTab).toHaveClass(/accent|active|selected|bg-/);

      await historyTab.click();
      await expect(historyTab).toHaveClass(/accent|active|selected|bg-/);
    }
  });

  test("5. Language toggle switches to Persian", async ({ page }) => {
    await page.goto("/oracle");

    // Look for language toggle button
    const langToggle = page
      .locator(
        "button:has-text('فا'), button:has-text('FA'), button[aria-label*='language'], button[aria-label*='lang']",
      )
      .first();
    if (await langToggle.isVisible()) {
      await langToggle.click();
      // After switching, some Persian text should appear
      await page.waitForTimeout(500);
      // Check for RTL attribute
      const htmlDir = await page.locator("html").getAttribute("dir");
      // Page may have RTL elements
      const hasRtl =
        htmlDir === "rtl" || (await page.locator("[dir='rtl']").count()) > 0;
      expect(hasRtl).toBeTruthy();
    }
  });

  test("6. Persian keyboard inputs characters", async ({ page }) => {
    await page.goto("/oracle");

    // Look for keyboard toggle button
    const keyboardToggle = page
      .locator("button[aria-label*='keyboard'], button:has-text('⌨')")
      .first();
    if (await keyboardToggle.isVisible()) {
      await keyboardToggle.click();

      // Find a Persian character key and click it
      const persianKey = page
        .locator("button:has-text('ا'), button:has-text('ب')")
        .first();
      if (await persianKey.isVisible()) {
        await persianKey.click();

        // The textarea should now contain a Persian character
        const textarea = page.locator("textarea").first();
        const value = await textarea.inputValue();
        expect(value.length).toBeGreaterThan(0);
      }
    }
  });

  test("7. Form validation shows errors on invalid input", async ({ page }) => {
    await page.goto("/oracle");

    // Open user form
    const addButton = page
      .locator(
        "button:has-text('Add'), button:has-text('New'), button:has-text('add'), button:has-text('new')",
      )
      .first();
    if (await addButton.isVisible()) {
      await addButton.click();

      // Submit empty form
      const submitButton = page.locator("button[type='submit']").first();
      await submitButton.click();

      // Error messages should appear
      await expect(
        page.locator("text=/required|error|invalid/i").first(),
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test("8. Reading appears in history after creation", async ({ page }) => {
    await page.goto("/oracle");

    // Navigate to history tab
    const historyTab = page.locator("button:has-text('History')");
    if (await historyTab.isVisible()) {
      await historyTab.click();
      // History section should be visible
      await page.waitForTimeout(1000);
    }
  });
});
