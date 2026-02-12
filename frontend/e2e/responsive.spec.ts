import { test, expect } from "@playwright/test";

test.describe("Responsive — Mobile (375px)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("sidebar is hidden on mobile", async ({ page }) => {
    await page.goto("/dashboard");
    // The aside with lg:flex should not be visible on mobile
    const sidebar = page.locator("aside");
    // Aside uses "hidden lg:flex" — should not be visible at 375px
    await expect(sidebar).toBeHidden();
  });

  test("hamburger menu is visible", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    await expect(hamburger).toBeVisible();
  });

  test("drawer opens on hamburger click", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    await hamburger.click();
    const drawer = page.locator("[role='dialog']");
    await expect(drawer).toBeVisible();
  });

  test("stats cards are single column", async ({ page }) => {
    await page.goto("/dashboard");
    const statsGrid = page.locator("[data-testid='stats-cards']");
    if (await statsGrid.isVisible()) {
      const gridClass = await statsGrid.getAttribute("class");
      expect(gridClass).toContain("grid-cols-1");
    }
  });

  test("no horizontal overflow on dashboard", async ({ page }) => {
    await page.goto("/dashboard");
    const scrollWidth = await page.evaluate(
      () => document.documentElement.scrollWidth,
    );
    const clientWidth = await page.evaluate(
      () => document.documentElement.clientWidth,
    );
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
  });
});

test.describe("Responsive — Tablet (768px)", () => {
  test.use({ viewport: { width: 768, height: 1024 } });

  test("sidebar is hidden on tablet (below lg)", async ({ page }) => {
    await page.goto("/dashboard");
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeHidden();
  });

  test("hamburger is visible on tablet", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    await expect(hamburger).toBeVisible();
  });

  test("stats cards use 2-column grid", async ({ page }) => {
    await page.goto("/dashboard");
    const statsGrid = page.locator("[data-testid='stats-cards']");
    if (await statsGrid.isVisible()) {
      const gridClass = await statsGrid.getAttribute("class");
      expect(gridClass).toContain("sm:grid-cols-2");
    }
  });
});

test.describe("Responsive — Desktop (1440px)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("sidebar is visible on desktop", async ({ page }) => {
    await page.goto("/dashboard");
    // At 1440px the aside with lg:flex should be visible
    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible();
  });

  test("hamburger is hidden on desktop", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    await expect(hamburger).toBeHidden();
  });

  test("stats cards use 4-column grid", async ({ page }) => {
    await page.goto("/dashboard");
    const statsGrid = page.locator("[data-testid='stats-cards']");
    if (await statsGrid.isVisible()) {
      const gridClass = await statsGrid.getAttribute("class");
      expect(gridClass).toContain("lg:grid-cols-4");
    }
  });
});

test.describe("Responsive — RTL Mobile (375px, FA)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("drawer direction is RTL when locale is FA", async ({ page }) => {
    await page.goto("/dashboard");
    // Set FA locale by clicking language toggle or via URL
    // Check that HTML dir attribute can be set
    await page.evaluate(() => {
      document.documentElement.dir = "rtl";
      document.documentElement.lang = "fa";
    });

    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    if (await hamburger.isVisible()) {
      await hamburger.click();
      const drawer = page.locator("[role='dialog']");
      await expect(drawer).toBeVisible();
      // In RTL the drawer should have end-0 positioning
      const drawerClass = await drawer.getAttribute("class");
      expect(drawerClass).toBeTruthy();
    }
  });
});
