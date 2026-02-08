/**
 * localStorage-based mock for Oracle user CRUD.
 * Swap to real API by changing the import in useOracleUsers.ts.
 */

import type { OracleUser, OracleUserCreate, OracleUserUpdate } from "@/types";

const STORAGE_KEY = "nps_oracle_users";
const DELAY_MS = 150;

function delay(ms = DELAY_MS): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function readStore(): OracleUser[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeStore(users: OracleUser[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
}

function nextId(users: OracleUser[]): number {
  return users.length === 0 ? 1 : Math.max(...users.map((u) => u.id)) + 1;
}

export const mockOracleUsers = {
  async list(): Promise<OracleUser[]> {
    await delay();
    return readStore();
  },

  async get(id: number): Promise<OracleUser> {
    await delay();
    const user = readStore().find((u) => u.id === id);
    if (!user) throw new Error(`User ${id} not found`);
    return user;
  },

  async create(data: OracleUserCreate): Promise<OracleUser> {
    await delay();
    const users = readStore();
    const now = new Date().toISOString();
    const user: OracleUser = {
      id: nextId(users),
      ...data,
      created_at: now,
      updated_at: now,
    };
    users.push(user);
    writeStore(users);
    return user;
  },

  async update(id: number, data: OracleUserUpdate): Promise<OracleUser> {
    await delay();
    const users = readStore();
    const idx = users.findIndex((u) => u.id === id);
    if (idx === -1) throw new Error(`User ${id} not found`);
    users[idx] = {
      ...users[idx],
      ...data,
      updated_at: new Date().toISOString(),
    };
    writeStore(users);
    return users[idx];
  },

  async delete(id: number): Promise<void> {
    await delay();
    const users = readStore().filter((u) => u.id !== id);
    writeStore(users);
  },
};
