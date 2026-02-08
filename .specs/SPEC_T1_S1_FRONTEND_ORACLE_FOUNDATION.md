# SPEC: Frontend Oracle Foundation - T1-S1
**Estimated Duration:** 4-5 hours  
**Layer:** Layer 1 (Frontend)  
**Terminal:** Terminal 1  
**Phase:** Phase 3 (Frontend Development)  
**Session:** T1-S1 (Foundation + User Profiles)

---

## 🎯 TL;DR

- **Quick Win:** Fix Issue #1 (button text visibility in V3 master key dialog) - 30 minutes
- **V4 Setup:** Initialize React + TypeScript + Vite project structure (if new V4)
- **User Profiles:** Complete user management UI (create, edit, delete, select)
- **Oracle Foundation:** Layout structure with user selector and placeholders
- **API Integration:** Connect to Terminal 2 user endpoints (GET, POST, PUT, DELETE)
- **Deliverable:** Working user profile management + Oracle page skeleton
- **Verification:** 2-minute test with manual user CRUD operations

---

## 📋 OBJECTIVE

Create the foundational Oracle page with complete user profile management system, enabling users to create/edit/delete user profiles and select active user for Oracle readings.

**Success Metric:** User can create a profile, select it, and see Oracle page ready for readings (T1-S2).

---

## 🔍 CONTEXT

### Current State
- **V3:** Tkinter desktop GUI with Oracle functionality
- **V4:** Either new project OR existing partial implementation
- **Issue #1:** Button text not visible in V3 master key dialog (macOS screenshot shows gray text on white)

### What's Changing
1. **Quick Fix:** V3 GUI button visibility across all Tkinter windows
2. **New V4:** React Oracle page with user profile management
3. **Architecture:** Separate user state from Oracle logic for better organization

### Why
- User profiles needed for personalized readings (birthdate, mother's name → numerology)
- Foundation for T1-S2 (Oracle question functionality)
- Fix UX issue in V3 before focusing on V4

---

## ✅ PREREQUISITES

**Before starting this spec:**

- [ ] Terminal 2 Session 1 completed (User API endpoints exist)
  - Verification: `curl http://localhost:8000/api/users` returns 200
- [ ] Terminal 4 (Database) has `users` table
  - Verification: `psql -c "SELECT * FROM users LIMIT 1;"`
- [ ] Node.js 18+ installed
  - Verification: `node --version` (should be v18.x or higher)
- [ ] Claude Code CLI available
  - Verification: `claude --version`

---

## 🛠️ TOOLS TO USE

**Mandatory Tools:**
- ✅ **view:** Read `/mnt/skills/public/frontend-design/SKILL.md` BEFORE coding
- ✅ **view:** Read `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` (Layer 1 section)
- ✅ **Extended Thinking:** Design user profile state management approach
- ✅ **Subagents:** Parallel component creation (if 4+ components needed)

**Optional Tools:**
- **ask_user:** Confirm UI layout preference (tabs vs single page)
- **conversation_search:** Check for previous Oracle UI discussions

---

## 📦 REQUIREMENTS

### Functional Requirements

**Issue #1 Fix (V3 GUI):**
1. Master key dialog buttons must have visible text (dark text or contrasting background)
2. Audit all Tkinter buttons in V3 codebase for contrast issues
3. Apply consistent button styling across entire V3 GUI
4. Test on macOS (where issue was reported)

**User Profile Management:**
1. User selector dropdown (loads all users from API)
2. Create new user form with fields:
   - Name (required, max 100 chars)
   - Birthday (required, date picker)
   - Mother's name (required, max 100 chars)
3. Edit existing user (same form, pre-populated)
4. Delete user (with confirmation dialog)
5. Active user state persisted (localStorage or React Context)

**Oracle Page Layout:**
1. Clean, minimal design (old money aesthetic)
2. User selector always visible at top
3. Placeholder sections for:
   - Question/sign input (T1-S2)
   - Reading results (T1-S2)
   - Reading history (T1-S4)
4. Dark theme matching V3 aesthetic

### Non-Functional Requirements

**Performance:**
- Initial page load <2 seconds
- User selector dropdown <100ms to open
- API calls <500ms response time
- No UI blocking during API calls

**Quality:**
- Test coverage ≥90% for user management components
- TypeScript strict mode (no `any` types)
- Accessibility WCAG 2.1 AA minimum
- Responsive design (desktop + tablet)

**Security:**
- No sensitive data in localStorage (user IDs only, not full objects)
- Input validation (XSS prevention)
- API error messages user-friendly (no stack traces)

---

## 🏗️ IMPLEMENTATION PLAN

### Phase 0: Issue #1 Fix (V3 GUI) - Duration: 30 minutes

**Why first:** Quick win, improves V3 usability immediately, clears the backlog item.

#### Tasks:

**0.1: Audit V3 Button Styling (10 min)**
```bash
# Search for all Tkinter Button widgets
cd /path/to/v3/nps
grep -r "tk.Button\|ttk.Button" gui/

# Identify buttons with potential visibility issues
# Look for: bg="white", fg="gray", or missing foreground colors
```

**Expected findings:**
- Master key dialog buttons (confirmed issue)
- Potentially other dialogs with white backgrounds

**0.2: Apply Fix (15 min)**

**File:** `gui/dialogs/master_key_dialog.py` (or similar)

**Change:**
```python
# BEFORE (invisible text)
save_button = tk.Button(
    dialog,
    text="Save",
    bg="white",  # White background
    fg="gray"    # Gray text - NOT VISIBLE!
)

# AFTER (visible text)
save_button = tk.Button(
    dialog,
    text="Save",
    bg="white",
    fg="#1a1a1a",      # Dark text for contrast
    activeforeground="white",
    activebackground="#2d5f8d"  # Blue when clicked
)
```

**Apply to all buttons in V3:**
- Find all `tk.Button` instances with `bg="white"`
- Add `fg="#1a1a1a"` (dark text)
- Add `activeforeground="white"` and `activebackground="#2d5f8d"`

**0.3: Test on macOS (5 min)**

**Verification:**
```bash
cd /path/to/v3/nps
python nps.py

# Manual test:
1. Open master key dialog
2. Verify button text clearly visible
3. Test all other dialogs (Hunter, Oracle, Vault, Memory)
4. Screenshot each dialog
```

**Checkpoint:**
- [ ] All buttons have visible text (dark on light, light on dark)
- [ ] Tested on macOS (where issue reported)
- [ ] No regressions (existing functionality still works)

**STOP if checkpoint fails:** Fix button styling before proceeding to V4.

---

### Phase 1: V4 Project Setup (if new) - Duration: 45 minutes

**Skip this phase if V4 project already exists with working structure.**

**Check if V4 exists:**
```bash
ls /path/to/nps-v4/frontend/web-ui/
# If exists with package.json → SKIP Phase 1
# If missing → EXECUTE Phase 1
```

#### Tasks:

**1.1: Create React + Vite Project (15 min)**

```bash
cd /path/to/nps-v4/frontend/
npm create vite@latest web-ui -- --template react-ts
cd web-ui
npm install
```

**Expected structure:**
```
web-ui/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**1.2: Install Dependencies (10 min)**

```bash
npm install react-router-dom axios @tanstack/react-query
npm install -D @types/react-router-dom
npm install -D eslint prettier eslint-config-prettier
npm install -D @testing-library/react @testing-library/jest-dom vitest jsdom
```

**Dependencies explained:**
- `react-router-dom`: Page navigation
- `axios`: API calls (simpler than fetch)
- `@tanstack/react-query`: API state management + caching
- `eslint + prettier`: Code quality
- `@testing-library/react`: Component testing

**1.3: Project Structure (10 min)**

```bash
mkdir -p src/{pages,components,services,hooks,types,utils}
```

**Create structure:**
```
src/
├── pages/
│   ├── Dashboard.tsx       (T1-S3)
│   ├── Scanner.tsx         (T1-S5)
│   ├── Oracle.tsx          (THIS SESSION)
│   ├── Vault.tsx           (T1-S6)
│   ├── Learning.tsx        (T1-S7)
│   └── Settings.tsx        (T1-S8)
├── components/
│   ├── UserSelector.tsx    (THIS SESSION)
│   ├── UserForm.tsx        (THIS SESSION)
│   └── Layout.tsx          (T1-S3)
├── services/
│   └── api.ts              (THIS SESSION - user endpoints)
├── hooks/
│   └── useUsers.ts         (THIS SESSION - React Query)
├── types/
│   └── user.ts             (THIS SESSION)
└── utils/
    └── constants.ts
```

**1.4: TypeScript Configuration (10 min)**

**File:** `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Key settings:**
- `strict: true` - No `any` types allowed
- `noUnusedLocals: true` - Clean code enforcement
- `paths` - Import aliases (`@/components/UserSelector`)

**Checkpoint:**
- [ ] `npm run dev` starts development server
- [ ] Browser shows Vite + React default page at http://localhost:5173
- [ ] No TypeScript errors (`npm run build` succeeds)
- [ ] Directory structure matches architecture plan

**STOP if checkpoint fails:** Fix project setup before creating components.

---

### Phase 2: User Types & API Service - Duration: 30 minutes

#### Tasks:

**2.1: User Types (10 min)**

**File:** `src/types/user.ts`

```typescript
/**
 * User profile for Oracle readings
 * Used for personalized numerology calculations
 */
export interface User {
  /** Unique identifier from database */
  id: number;
  
  /** User's full name (max 100 chars) */
  name: string;
  
  /** Birthday for numerology calculations (ISO 8601 format) */
  birthday: string;
  
  /** Mother's name for numerology (max 100 chars) */
  mothers_name: string;
  
  /** Timestamp of creation */
  created_at: string;
  
  /** Timestamp of last update */
  updated_at: string;
}

/**
 * User creation payload (no ID)
 */
export interface CreateUserPayload {
  name: string;
  birthday: string;
  mothers_name: string;
}

/**
 * User update payload (partial)
 */
export interface UpdateUserPayload {
  name?: string;
  birthday?: string;
  mothers_name?: string;
}

/**
 * API response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

/**
 * API error response
 */
export interface ApiError {
  detail: string;
  status_code: number;
}
```

**2.2: API Service (20 min)**

**File:** `src/services/api.ts`

```typescript
import axios, { AxiosError } from 'axios';
import type { User, CreateUserPayload, UpdateUserPayload, ApiResponse, ApiError } from '@/types/user';

/**
 * Base API configuration
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 5000; // 5 seconds

/**
 * Axios instance with base configuration
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Add API key to all requests (if available)
 */
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('nps_api_key');
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

/**
 * Handle API errors consistently
 */
function handleApiError(error: AxiosError<ApiError>): never {
  if (error.response) {
    // Server responded with error
    throw new Error(error.response.data.detail || 'API request failed');
  } else if (error.request) {
    // Request sent but no response
    throw new Error('No response from server. Check if API is running.');
  } else {
    // Request setup error
    throw new Error(error.message);
  }
}

/**
 * User API endpoints
 */
export const userApi = {
  /**
   * Get all users
   */
  async getAll(): Promise<User[]> {
    try {
      const response = await apiClient.get<ApiResponse<User[]>>('/api/users');
      return response.data.data;
    } catch (error) {
      return handleApiError(error as AxiosError<ApiError>);
    }
  },

  /**
   * Get user by ID
   */
  async getById(id: number): Promise<User> {
    try {
      const response = await apiClient.get<ApiResponse<User>>(`/api/users/${id}`);
      return response.data.data;
    } catch (error) {
      return handleApiError(error as AxiosError<ApiError>);
    }
  },

  /**
   * Create new user
   */
  async create(payload: CreateUserPayload): Promise<User> {
    try {
      const response = await apiClient.post<ApiResponse<User>>('/api/users', payload);
      return response.data.data;
    } catch (error) {
      return handleApiError(error as AxiosError<ApiError>);
    }
  },

  /**
   * Update existing user
   */
  async update(id: number, payload: UpdateUserPayload): Promise<User> {
    try {
      const response = await apiClient.put<ApiResponse<User>>(`/api/users/${id}`, payload);
      return response.data.data;
    } catch (error) {
      return handleApiError(error as AxiosError<ApiError>);
    }
  },

  /**
   * Delete user
   */
  async delete(id: number): Promise<void> {
    try {
      await apiClient.delete(`/api/users/${id}`);
    } catch (error) {
      return handleApiError(error as AxiosError<ApiError>);
    }
  },
};
```

**Checkpoint:**
- [ ] TypeScript types compile (no errors)
- [ ] API service can be imported: `import { userApi } from '@/services/api';`
- [ ] Environment variable handling works (`VITE_API_URL`)
- [ ] Error handling includes user-friendly messages

**STOP if checkpoint fails:** Fix types/API service before creating hooks.

---

### Phase 3: React Query Hooks - Duration: 30 minutes

**Why React Query:** Handles caching, loading states, error states, and refetching automatically.

#### Tasks:

**3.1: React Query Setup (10 min)**

**File:** `src/main.tsx`

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

/**
 * React Query configuration
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
      retry: 1, // Retry failed requests once
      refetchOnWindowFocus: false, // Don't refetch on tab focus
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

**3.2: User Hooks (20 min)**

**File:** `src/hooks/useUsers.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/services/api';
import type { User, CreateUserPayload, UpdateUserPayload } from '@/types/user';

/**
 * Query key factory for users
 */
const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: string) => [...userKeys.lists(), { filters }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: number) => [...userKeys.details(), id] as const,
};

/**
 * Hook: Get all users
 */
export function useUsers() {
  return useQuery({
    queryKey: userKeys.lists(),
    queryFn: () => userApi.getAll(),
  });
}

/**
 * Hook: Get user by ID
 */
export function useUser(id: number) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => userApi.getById(id),
    enabled: !!id, // Only fetch if ID exists
  });
}

/**
 * Hook: Create user
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateUserPayload) => userApi.create(payload),
    onSuccess: () => {
      // Invalidate users list to trigger refetch
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

/**
 * Hook: Update user
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateUserPayload }) =>
      userApi.update(id, payload),
    onSuccess: (updatedUser) => {
      // Update cache with new user data
      queryClient.setQueryData(userKeys.detail(updatedUser.id), updatedUser);
      // Invalidate list to refresh
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

/**
 * Hook: Delete user
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => userApi.delete(id),
    onSuccess: () => {
      // Invalidate list to trigger refetch
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}
```

**Checkpoint:**
- [ ] Hooks can be imported: `import { useUsers } from '@/hooks/useUsers';`
- [ ] TypeScript recognizes all hook types
- [ ] Query keys follow consistent pattern
- [ ] Cache invalidation logic correct

**STOP if checkpoint fails:** Fix hooks before creating components.

---

### Phase 4: User Selector Component - Duration: 45 minutes

#### Tasks:

**4.1: UserSelector Component (30 min)**

**File:** `src/components/UserSelector.tsx`

```typescript
import React from 'react';
import { useUsers } from '@/hooks/useUsers';
import type { User } from '@/types/user';

interface UserSelectorProps {
  /** Currently selected user ID */
  selectedUserId: number | null;
  
  /** Callback when user selected */
  onUserSelect: (userId: number) => void;
  
  /** Optional className for styling */
  className?: string;
}

/**
 * User selector dropdown component
 * 
 * @example
 * <UserSelector 
 *   selectedUserId={activeUserId} 
 *   onUserSelect={setActiveUserId} 
 * />
 */
export const UserSelector: React.FC<UserSelectorProps> = ({
  selectedUserId,
  onUserSelect,
  className = '',
}) => {
  const { data: users, isLoading, error } = useUsers();

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const userId = parseInt(event.target.value, 10);
    if (!isNaN(userId)) {
      onUserSelect(userId);
    }
  };

  if (isLoading) {
    return (
      <div className={`user-selector-loading ${className}`}>
        <span className="loading-spinner"></span>
        <span>Loading users...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`user-selector-error ${className}`}>
        <span className="error-icon">⚠️</span>
        <span>Failed to load users: {(error as Error).message}</span>
      </div>
    );
  }

  if (!users || users.length === 0) {
    return (
      <div className={`user-selector-empty ${className}`}>
        <span>No users found. Create your first user profile!</span>
      </div>
    );
  }

  return (
    <div className={`user-selector ${className}`}>
      <label htmlFor="user-select" className="user-selector-label">
        Select User:
      </label>
      <select
        id="user-select"
        value={selectedUserId || ''}
        onChange={handleChange}
        className="user-selector-dropdown"
      >
        <option value="" disabled>
          -- Select a user --
        </option>
        {users.map((user) => (
          <option key={user.id} value={user.id}>
            {user.name}
          </option>
        ))}
      </select>
    </div>
  );
};
```

**4.2: UserSelector Styles (15 min)**

**File:** `src/components/UserSelector.css`

```css
/**
 * User Selector Component Styles
 * Old money aesthetic: minimal, premium, clean
 */

.user-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #2d2d2d;
}

.user-selector-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #e0e0e0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-selector-dropdown {
  flex: 1;
  max-width: 300px;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  color: #ffffff;
  background-color: #2d2d2d;
  border: 1px solid #404040;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-selector-dropdown:hover {
  border-color: #606060;
  background-color: #333333;
}

.user-selector-dropdown:focus {
  outline: none;
  border-color: #4a9eff;
  box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
}

/* Loading state */
.user-selector-loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  color: #a0a0a0;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #404040;
  border-top-color: #4a9eff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error state */
.user-selector-error {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  color: #ff6b6b;
  background-color: rgba(255, 107, 107, 0.1);
  border-radius: 6px;
}

.error-icon {
  font-size: 1.25rem;
}

/* Empty state */
.user-selector-empty {
  padding: 1rem;
  color: #a0a0a0;
  font-style: italic;
}
```

**Checkpoint:**
- [ ] Component renders without errors
- [ ] Dropdown shows all users from API
- [ ] Loading state displays during fetch
- [ ] Error state displays on API failure
- [ ] Empty state displays when no users
- [ ] Selection triggers `onUserSelect` callback
- [ ] Dark theme matches V3 aesthetic

**STOP if checkpoint fails:** Fix UserSelector before creating UserForm.

---

### Phase 5: User Form Component - Duration: 1 hour

#### Tasks:

**5.1: UserForm Component (40 min)**

**File:** `src/components/UserForm.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { useCreateUser, useUpdateUser } from '@/hooks/useUsers';
import type { User, CreateUserPayload } from '@/types/user';

interface UserFormProps {
  /** Existing user for edit mode (null for create mode) */
  user?: User | null;
  
  /** Callback on successful save */
  onSuccess?: () => void;
  
  /** Callback on cancel */
  onCancel?: () => void;
}

/**
 * User creation/edit form
 * 
 * @example
 * // Create mode
 * <UserForm onSuccess={() => setShowForm(false)} />
 * 
 * // Edit mode
 * <UserForm user={selectedUser} onSuccess={() => setShowForm(false)} />
 */
export const UserForm: React.FC<UserFormProps> = ({
  user = null,
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState<CreateUserPayload>({
    name: '',
    birthday: '',
    mothers_name: '',
  });
  const [errors, setErrors] = useState<Partial<CreateUserPayload>>({});

  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();

  const isEditMode = !!user;
  const isLoading = createMutation.isPending || updateMutation.isPending;

  // Pre-populate form in edit mode
  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name,
        birthday: user.birthday.split('T')[0], // Convert ISO to YYYY-MM-DD
        mothers_name: user.mothers_name,
      });
    }
  }, [user]);

  const validateForm = (): boolean => {
    const newErrors: Partial<CreateUserPayload> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.length > 100) {
      newErrors.name = 'Name must be 100 characters or less';
    }

    if (!formData.birthday) {
      newErrors.birthday = 'Birthday is required';
    }

    if (!formData.mothers_name.trim()) {
      newErrors.mothers_name = "Mother's name is required";
    } else if (formData.mothers_name.length > 100) {
      newErrors.mothers_name = "Mother's name must be 100 characters or less";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      if (isEditMode && user) {
        await updateMutation.mutateAsync({
          id: user.id,
          payload: formData,
        });
      } else {
        await createMutation.mutateAsync(formData);
      }

      // Reset form
      setFormData({ name: '', birthday: '', mothers_name: '' });
      setErrors({});

      // Notify parent
      onSuccess?.();
    } catch (error) {
      // Error handled by mutation (displayed below form)
    }
  };

  const handleChange = (field: keyof CreateUserPayload) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));

    // Clear error on change
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleCancel = () => {
    setFormData({ name: '', birthday: '', mothers_name: '' });
    setErrors({});
    onCancel?.();
  };

  const mutationError = createMutation.error || updateMutation.error;

  return (
    <form onSubmit={handleSubmit} className="user-form">
      <h3 className="user-form-title">
        {isEditMode ? 'Edit User Profile' : 'Create New User Profile'}
      </h3>

      {/* Name Field */}
      <div className="form-field">
        <label htmlFor="name" className="form-label">
          Name <span className="required">*</span>
        </label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={handleChange('name')}
          className={`form-input ${errors.name ? 'error' : ''}`}
          placeholder="Enter your name"
          maxLength={100}
          disabled={isLoading}
        />
        {errors.name && (
          <span className="form-error">{errors.name}</span>
        )}
      </div>

      {/* Birthday Field */}
      <div className="form-field">
        <label htmlFor="birthday" className="form-label">
          Birthday <span className="required">*</span>
        </label>
        <input
          id="birthday"
          type="date"
          value={formData.birthday}
          onChange={handleChange('birthday')}
          className={`form-input ${errors.birthday ? 'error' : ''}`}
          disabled={isLoading}
        />
        {errors.birthday && (
          <span className="form-error">{errors.birthday}</span>
        )}
      </div>

      {/* Mother's Name Field */}
      <div className="form-field">
        <label htmlFor="mothers_name" className="form-label">
          Mother's Name <span className="required">*</span>
        </label>
        <input
          id="mothers_name"
          type="text"
          value={formData.mothers_name}
          onChange={handleChange('mothers_name')}
          className={`form-input ${errors.mothers_name ? 'error' : ''}`}
          placeholder="Enter your mother's name"
          maxLength={100}
          disabled={isLoading}
        />
        {errors.mothers_name && (
          <span className="form-error">{errors.mothers_name}</span>
        )}
      </div>

      {/* Mutation Error */}
      {mutationError && (
        <div className="form-mutation-error">
          <span className="error-icon">⚠️</span>
          <span>{(mutationError as Error).message}</span>
        </div>
      )}

      {/* Actions */}
      <div className="form-actions">
        <button
          type="button"
          onClick={handleCancel}
          className="btn btn-secondary"
          disabled={isLoading}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading
            ? 'Saving...'
            : isEditMode
            ? 'Update User'
            : 'Create User'}
        </button>
      </div>
    </form>
  );
};
```

**5.2: UserForm Styles (20 min)**

**File:** `src/components/UserForm.css`

```css
/**
 * User Form Component Styles
 */

.user-form {
  max-width: 500px;
  padding: 2rem;
  background-color: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #2d2d2d;
}

.user-form-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 500;
  color: #ffffff;
  letter-spacing: 0.02em;
}

/* Form Fields */
.form-field {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #e0e0e0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.required {
  color: #ff6b6b;
  margin-left: 0.25rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  color: #ffffff;
  background-color: #2d2d2d;
  border: 1px solid #404040;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.form-input:hover {
  border-color: #606060;
}

.form-input:focus {
  outline: none;
  border-color: #4a9eff;
  box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
}

.form-input.error {
  border-color: #ff6b6b;
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-error {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #ff6b6b;
}

/* Mutation Error */
.form-mutation-error {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
  color: #ff6b6b;
  background-color: rgba(255, 107, 107, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(255, 107, 107, 0.3);
}

/* Form Actions */
.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.btn {
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  color: #ffffff;
  background-color: #4a9eff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #3a8eef;
}

.btn-secondary {
  color: #e0e0e0;
  background-color: #2d2d2d;
  border: 1px solid #404040;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #3d3d3d;
}
```

**Checkpoint:**
- [ ] Form renders in create mode (no user prop)
- [ ] Form renders in edit mode (with user prop, fields pre-populated)
- [ ] Validation works (required fields, max length)
- [ ] Create user mutation succeeds
- [ ] Update user mutation succeeds
- [ ] Error messages display appropriately
- [ ] Form resets after successful submission
- [ ] Cancel button clears form

**STOP if checkpoint fails:** Fix UserForm before creating Oracle page.

---

### Phase 6: Oracle Page Layout - Duration: 1 hour

#### Tasks:

**6.1: Oracle Page Component (45 min)**

**File:** `src/pages/Oracle.tsx`

```typescript
import React, { useState } from 'react';
import { UserSelector } from '@/components/UserSelector';
import { UserForm } from '@/components/UserForm';
import { useDeleteUser } from '@/hooks/useUsers';
import type { User } from '@/types/user';
import './Oracle.css';

/**
 * Oracle page with user profile management
 * 
 * Features:
 * - User selector at top
 * - Create/Edit user forms
 * - Delete user with confirmation
 * - Placeholders for Oracle functionality (T1-S2, T1-S3, T1-S4)
 */
export const Oracle: React.FC = () => {
  const [activeUserId, setActiveUserId] = useState<number | null>(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('nps_active_user_id');
    return saved ? parseInt(saved, 10) : null;
  });

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const deleteMutation = useDeleteUser();

  // Persist active user to localStorage
  const handleUserSelect = (userId: number) => {
    setActiveUserId(userId);
    localStorage.setItem('nps_active_user_id', userId.toString());
  };

  const handleDeleteUser = async () => {
    if (!activeUserId) return;

    try {
      await deleteMutation.mutateAsync(activeUserId);
      setActiveUserId(null);
      localStorage.removeItem('nps_active_user_id');
      setShowDeleteConfirm(false);
    } catch (error) {
      // Error handled by mutation
    }
  };

  return (
    <div className="oracle-page">
      {/* Header */}
      <header className="oracle-header">
        <h1 className="oracle-title">Oracle</h1>
        <p className="oracle-subtitle">
          Cosmic Guidance & Numerology Readings
        </p>
      </header>

      {/* User Profile Section */}
      <section className="oracle-section user-profile-section">
        <h2 className="section-title">User Profile</h2>

        <UserSelector
          selectedUserId={activeUserId}
          onUserSelect={handleUserSelect}
          className="oracle-user-selector"
        />

        <div className="user-actions">
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn btn-primary"
          >
            + Create New User
          </button>

          {activeUserId && (
            <>
              <button
                onClick={() => setShowEditForm(true)}
                className="btn btn-secondary"
              >
                Edit User
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="btn btn-danger"
              >
                Delete User
              </button>
            </>
          )}
        </div>

        {/* Create Form Modal */}
        {showCreateForm && (
          <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <UserForm
                onSuccess={() => setShowCreateForm(false)}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        )}

        {/* Edit Form Modal */}
        {showEditForm && activeUserId && (
          <div className="modal-overlay" onClick={() => setShowEditForm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <UserForm
                user={{ id: activeUserId } as User}
                onSuccess={() => setShowEditForm(false)}
                onCancel={() => setShowEditForm(false)}
              />
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="modal-overlay" onClick={() => setShowDeleteConfirm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="confirm-dialog">
                <h3>Delete User?</h3>
                <p>
                  Are you sure you want to delete this user profile?
                  This action cannot be undone.
                </p>
                <div className="confirm-actions">
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="btn btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteUser}
                    className="btn btn-danger"
                    disabled={deleteMutation.isPending}
                  >
                    {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Oracle Reading Section (Placeholder - T1-S2) */}
      <section className="oracle-section oracle-reading-section">
        <h2 className="section-title">Oracle Reading</h2>
        <div className="placeholder">
          <p>🔮 Question & Time Sign Input</p>
          <p className="placeholder-note">Coming in T1-S2</p>
        </div>
      </section>

      {/* Reading Results Section (Placeholder - T1-S2) */}
      <section className="oracle-section reading-results-section">
        <h2 className="section-title">Reading Results</h2>
        <div className="placeholder">
          <p>📜 FC60 Interpretation Display</p>
          <p className="placeholder-note">Coming in T1-S2</p>
        </div>
      </section>

      {/* Reading History Section (Placeholder - T1-S4) */}
      <section className="oracle-section reading-history-section">
        <h2 className="section-title">Reading History</h2>
        <div className="placeholder">
          <p>📚 Past Readings & Insights</p>
          <p className="placeholder-note">Coming in T1-S4</p>
        </div>
      </section>
    </div>
  );
};
```

**6.2: Oracle Page Styles (15 min)**

**File:** `src/pages/Oracle.css`

```css
/**
 * Oracle Page Styles
 * Old money aesthetic: minimal, premium, clean
 */

.oracle-page {
  min-height: 100vh;
  padding: 2rem;
  background-color: #0d0d0d;
  color: #ffffff;
}

/* Header */
.oracle-header {
  margin-bottom: 3rem;
  text-align: center;
}

.oracle-title {
  margin: 0 0 0.5rem;
  font-size: 2.5rem;
  font-weight: 300;
  letter-spacing: 0.1em;
  color: #ffffff;
}

.oracle-subtitle {
  margin: 0;
  font-size: 1rem;
  font-weight: 400;
  color: #a0a0a0;
  letter-spacing: 0.05em;
}

/* Sections */
.oracle-section {
  margin-bottom: 2rem;
  padding: 2rem;
  background-color: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #2d2d2d;
}

.section-title {
  margin: 0 0 1.5rem;
  font-size: 1.25rem;
  font-weight: 500;
  color: #e0e0e0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #2d2d2d;
  padding-bottom: 0.75rem;
}

/* User Actions */
.user-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.btn-danger {
  color: #ffffff;
  background-color: #dc3545;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c82333;
}

/* Placeholders */
.placeholder {
  padding: 3rem 2rem;
  text-align: center;
  background-color: #2d2d2d;
  border-radius: 6px;
  border: 2px dashed #404040;
}

.placeholder p {
  margin: 0.5rem 0;
  font-size: 1.125rem;
  color: #a0a0a0;
}

.placeholder-note {
  font-size: 0.875rem !important;
  font-style: italic;
  color: #606060 !important;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: #1a1a1a;
  border-radius: 8px;
  padding: 0;
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
}

/* Confirm Dialog */
.confirm-dialog {
  padding: 2rem;
  max-width: 400px;
}

.confirm-dialog h3 {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  color: #ffffff;
}

.confirm-dialog p {
  margin: 0 0 1.5rem;
  color: #a0a0a0;
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}
```

**Checkpoint:**
- [ ] Page renders without errors
- [ ] User selector works (loads users, selection persists in localStorage)
- [ ] Create user modal opens/closes
- [ ] Edit user modal opens/closes (only when user selected)
- [ ] Delete confirmation modal works
- [ ] Delete user mutation succeeds
- [ ] Placeholder sections visible for T1-S2, T1-S4
- [ ] Dark theme matches V3 aesthetic
- [ ] Responsive on desktop + tablet

**STOP if checkpoint fails:** Fix Oracle page before adding routing.

---

### Phase 7: Routing & Integration - Duration: 30 minutes

#### Tasks:

**7.1: App Routing (20 min)**

**File:** `src/App.tsx`

```typescript
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Oracle } from './pages/Oracle';
import './App.css';

/**
 * Main App component with routing
 */
function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          {/* Default route → Oracle page (for now) */}
          <Route path="/" element={<Navigate to="/oracle" replace />} />
          
          {/* Oracle page */}
          <Route path="/oracle" element={<Oracle />} />
          
          {/* Placeholder routes for other pages */}
          <Route path="/dashboard" element={<div>Dashboard (T1-S3)</div>} />
          <Route path="/scanner" element={<div>Scanner (T1-S5)</div>} />
          <Route path="/vault" element={<div>Vault (T1-S6)</div>} />
          <Route path="/learning" element={<div>Learning (T1-S7)</div>} />
          <Route path="/settings" element={<div>Settings (T1-S8)</div>} />
          
          {/* 404 */}
          <Route path="*" element={<div>404 - Page Not Found</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

**7.2: Global Styles (10 min)**

**File:** `src/App.css`

```css
/**
 * Global App Styles
 */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #0d0d0d;
  color: #ffffff;
}

.app {
  min-height: 100vh;
}

/* Utility classes */
.text-center {
  text-align: center;
}

.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }
.mt-4 { margin-top: 2rem; }

.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 2rem; }
```

**Checkpoint:**
- [ ] App compiles without errors
- [ ] Navigating to http://localhost:5173/ redirects to /oracle
- [ ] Oracle page loads and functions correctly
- [ ] Placeholder routes work (Dashboard, Scanner, Vault, etc.)
- [ ] 404 page displays for invalid routes

**STOP if checkpoint fails:** Fix routing before writing tests.

---

### Phase 8: Component Tests - Duration: 45 minutes

#### Tasks:

**8.1: Test Setup (10 min)**

**File:** `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

**File:** `src/test/setup.ts`

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

**8.2: UserSelector Tests (15 min)**

**File:** `src/components/UserSelector.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserSelector } from './UserSelector';
import { userApi } from '@/services/api';

// Mock API
vi.mock('@/services/api', () => ({
  userApi: {
    getAll: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('UserSelector', () => {
  it('renders loading state initially', () => {
    vi.mocked(userApi.getAll).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <UserSelector selectedUserId={null} onUserSelect={() => {}} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  it('renders users in dropdown', async () => {
    const mockUsers = [
      { id: 1, name: 'Alice', birthday: '1990-01-01', mothers_name: 'Mom1', created_at: '', updated_at: '' },
      { id: 2, name: 'Bob', birthday: '1992-02-02', mothers_name: 'Mom2', created_at: '', updated_at: '' },
    ];

    vi.mocked(userApi.getAll).mockResolvedValue(mockUsers);

    render(
      <UserSelector selectedUserId={null} onUserSelect={() => {}} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });
  });

  it('displays error state on API failure', async () => {
    vi.mocked(userApi.getAll).mockRejectedValue(new Error('API Error'));

    render(
      <UserSelector selectedUserId={null} onUserSelect={() => {}} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load users/)).toBeInTheDocument();
    });
  });

  it('displays empty state when no users', async () => {
    vi.mocked(userApi.getAll).mockResolvedValue([]);

    render(
      <UserSelector selectedUserId={null} onUserSelect={() => {}} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/No users found/)).toBeInTheDocument();
    });
  });
});
```

**8.3: UserForm Tests (20 min)**

**File:** `src/components/UserForm.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserForm } from './UserForm';
import { userApi } from '@/services/api';

vi.mock('@/services/api', () => ({
  userApi: {
    create: vi.fn(),
    update: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('UserForm', () => {
  it('renders create mode by default', () => {
    render(<UserForm />, { wrapper: createWrapper() });
    
    expect(screen.getByText('Create New User Profile')).toBeInTheDocument();
    expect(screen.getByText('Create User')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<UserForm />, { wrapper: createWrapper() });

    const submitButton = screen.getByText('Create User');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
      expect(screen.getByText('Birthday is required')).toBeInTheDocument();
      expect(screen.getByText("Mother's name is required")).toBeInTheDocument();
    });
  });

  it('creates user successfully', async () => {
    const mockCreate = vi.mocked(userApi.create);
    mockCreate.mockResolvedValue({
      id: 1,
      name: 'Alice',
      birthday: '1990-01-01',
      mothers_name: 'Mom',
      created_at: '',
      updated_at: '',
    });

    const onSuccess = vi.fn();

    render(<UserForm onSuccess={onSuccess} />, { wrapper: createWrapper() });

    // Fill form
    fireEvent.change(screen.getByLabelText(/Name/), {
      target: { value: 'Alice' },
    });
    fireEvent.change(screen.getByLabelText(/Birthday/), {
      target: { value: '1990-01-01' },
    });
    fireEvent.change(screen.getByLabelText(/Mother's Name/), {
      target: { value: 'Mom' },
    });

    // Submit
    fireEvent.click(screen.getByText('Create User'));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        name: 'Alice',
        birthday: '1990-01-01',
        mothers_name: 'Mom',
      });
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('renders edit mode with pre-populated data', () => {
    const mockUser = {
      id: 1,
      name: 'Alice',
      birthday: '1990-01-01T00:00:00Z',
      mothers_name: 'Mom',
      created_at: '',
      updated_at: '',
    };

    render(<UserForm user={mockUser} />, { wrapper: createWrapper() });

    expect(screen.getByText('Edit User Profile')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Alice')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Mom')).toBeInTheDocument();
  });
});
```

**Checkpoint:**
- [ ] Test suite runs: `npm test`
- [ ] All tests pass (10+ tests)
- [ ] Coverage ≥90% for UserSelector and UserForm
- [ ] No console errors during tests
- [ ] Tests include loading, error, and success states

**STOP if checkpoint fails:** Fix tests before final verification.

---

## ✅ VERIFICATION CHECKLIST

### Complete System Verification (2 Minutes)

**Terminal 1: Development Server**
```bash
cd frontend/web-ui
npm run dev
```

**Terminal 2: Manual Testing**
```bash
# 1. Open browser to http://localhost:5173/oracle
# Expected: Oracle page loads with user selector

# 2. Create a new user
#    - Click "Create New User"
#    - Fill form: Name="Test User", Birthday="2000-01-01", Mother's Name="Test Mom"
#    - Click "Create User"
# Expected: Modal closes, user appears in dropdown, user selected

# 3. Edit the user
#    - Click "Edit User"
#    - Change name to "Updated User"
#    - Click "Update User"
# Expected: Modal closes, dropdown shows "Updated User"

# 4. Delete the user
#    - Click "Delete User"
#    - Confirm deletion
# Expected: User removed from dropdown, active user cleared

# 5. Refresh page
# Expected: Previously selected user still selected (localStorage)
```

**Terminal 3: Run Tests**
```bash
npm test
# Expected: All tests pass (10+ tests, 90%+ coverage)
```

**Terminal 4: Issue #1 Verification (V3)**
```bash
cd /path/to/v3/nps
python nps.py

# Manual test:
# 1. Open master key dialog
# 2. Verify button text clearly visible (dark text on white background)
# 3. Test other dialogs (Hunter, Oracle, Vault, Memory)
# Expected: All buttons have visible text
```

**Terminal 5: Build Check**
```bash
cd frontend/web-ui
npm run build
# Expected: Build succeeds, dist/ folder created
```

---

## 🎯 SUCCESS CRITERIA

### Mandatory Pass Criteria

**Issue #1 (V3):**
- [ ] Master key dialog buttons have visible text
- [ ] All Tkinter buttons audited for contrast
- [ ] Consistent button styling applied
- [ ] Tested on macOS (screenshot confirms fix)

**V4 React Project:**
- [ ] React + TypeScript + Vite project set up
- [ ] Dependencies installed (react-router-dom, axios, react-query)
- [ ] Project structure matches architecture plan
- [ ] TypeScript strict mode enabled

**User Profile Management:**
- [ ] User selector loads all users from API
- [ ] Create user form validates and submits
- [ ] Edit user form pre-populates and updates
- [ ] Delete user with confirmation works
- [ ] Active user persists in localStorage
- [ ] Error handling for API failures

**Oracle Page Layout:**
- [ ] Clean, minimal design (old money aesthetic)
- [ ] User selector always visible at top
- [ ] Placeholder sections for T1-S2 (reading input + results)
- [ ] Placeholder section for T1-S4 (reading history)
- [ ] Dark theme matches V3 aesthetic
- [ ] Responsive on desktop + tablet

**Testing:**
- [ ] Test coverage ≥90% for UserSelector and UserForm
- [ ] All tests pass (10+ tests)
- [ ] No console errors
- [ ] Build succeeds

**Performance:**
- [ ] Initial page load <2 seconds
- [ ] User selector dropdown <100ms
- [ ] API calls <500ms
- [ ] No UI blocking

**Code Quality:**
- [ ] TypeScript strict mode (no `any` types)
- [ ] Proper error handling (user-friendly messages)
- [ ] Accessibility WCAG 2.1 AA
- [ ] Clean code (ESLint + Prettier)

---

## 🔄 HANDOFF TO NEXT SESSION

### If Session Ends Mid-Implementation:

**Resume from Phase:** [N]

**Context needed:**
- Which phase completed? (verify with checkpoints)
- Any API endpoints not yet available?
- Any failing tests?

**Verification before continuing:**
```bash
# Check which phases completed
npm test                  # Should pass for completed components
npm run dev               # Should start without errors
curl http://localhost:8000/api/users  # Should return users
```

---

## 📝 NEXT STEPS (After This Session)

**T1-S2: Oracle Question Functionality**
1. Create question input component (FC60 calculation)
2. Create time sign selector (60 hexagrams)
3. Integrate with Oracle API endpoint (Terminal 2)
4. Display reading results (FC60 interpretation)
5. Test end-to-end Oracle reading flow

**T1-S3: Dashboard Page**
1. Create multi-terminal scanner status cards
2. Create health dots for service monitoring
3. Integrate with API health endpoints

**T1-S4: Oracle Reading History**
1. Create reading history table component
2. Integrate with history API endpoint
3. Add search/filter functionality
4. Export readings to CSV/JSON

---

## 🎓 LESSONS & PATTERNS

**React Query Best Practices:**
- Use query key factories for consistency
- Invalidate queries after mutations
- Handle loading, error, and empty states
- Enable queries conditionally (e.g., `enabled: !!id`)

**Form Validation Pattern:**
- Validate on submit, not on every keystroke
- Clear errors on field change
- Provide user-friendly error messages
- Disable submit during loading

**Modal Pattern:**
- Click overlay to close
- Stop propagation on modal content
- Clean up state on close
- Disable body scroll when open (TODO: add this)

**API Error Handling:**
- Consistent error interface
- User-friendly messages (no stack traces)
- Retry logic for transient failures
- Fallback UI for errors

---

## 🔍 TROUBLESHOOTING

**Issue: API calls fail with CORS error**
```bash
# Solution: Add CORS middleware to FastAPI (Terminal 2)
# In api/app/main.py:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue: React Query not refetching after mutation**
```typescript
// Solution: Ensure query invalidation after mutation
useMutation({
  mutationFn: userApi.create,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: userKeys.lists() });
  },
});
```

**Issue: TypeScript errors for import aliases**
```bash
# Solution: Update vite.config.ts
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

**Issue: Tests fail with "document is not defined"**
```typescript
// Solution: Add jsdom environment to vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
  },
});
```

---

## 💡 CONFIDENCE LEVEL

**High (95%)** - Standard React patterns with well-defined requirements

**Assumptions:**
- Terminal 2 user API endpoints exist and return expected format
- Database has `users` table with correct schema
- V3 codebase accessible for Issue #1 fix

**Risks:**
- API endpoint format mismatch (mitigated by TypeScript types)
- V3 GUI code structure unknown (will adapt during Phase 0)

---

**END OF SPEC**

*Ready for Claude Code CLI execution with Extended Thinking*  
*Estimated Total Duration: 4-5 hours*  
*Next Session: T1-S2 (Oracle Question Functionality)*
