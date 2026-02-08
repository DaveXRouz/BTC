import { Page } from "@playwright/test";

const API_BASE = "http://localhost:8000";

/**
 * Create a test user via API for E2E tests.
 * Returns the user ID.
 */
export async function createTestUser(
  page: Page,
  name: string = "E2E_TestUser",
): Promise<number> {
  const response = await page.request.post(`${API_BASE}/api/oracle/users`, {
    data: {
      name,
      birthday: "1990-06-15",
      mother_name: "E2E_Mother",
      country: "US",
      city: "Test City",
    },
    headers: {
      Authorization: `Bearer ${process.env.API_SECRET_KEY || "changeme-generate-a-real-secret"}`,
      "Content-Type": "application/json",
    },
  });
  const data = await response.json();
  return data.id;
}

/**
 * Clean up test users created during E2E tests.
 */
export async function cleanupTestUsers(page: Page): Promise<void> {
  const response = await page.request.get(
    `${API_BASE}/api/oracle/users?search=E2E_`,
    {
      headers: {
        Authorization: `Bearer ${process.env.API_SECRET_KEY || "changeme-generate-a-real-secret"}`,
      },
    },
  );
  const data = await response.json();
  for (const user of data.users || []) {
    await page.request.delete(`${API_BASE}/api/oracle/users/${user.id}`, {
      headers: {
        Authorization: `Bearer ${process.env.API_SECRET_KEY || "changeme-generate-a-real-secret"}`,
      },
    });
  }
}
