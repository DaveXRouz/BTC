# File Creation Templates

> Flexible templates — follow the STRUCTURE, adapt the CONTENT to the task.
> When touching existing files that don't match these patterns, upgrade them.

---

## Python Module Template

```python
"""
[Module Name] — [One-line description]

[Optional: 2-3 sentence explanation of what this module does and why it exists.]
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Add type-only imports here

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════

# [Define constants here if needed]

# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


class ClassName:
    """Brief description.

    Attributes:
        attr1: Description.
        attr2: Description.
    """

    def __init__(self, ...) -> None:
        """Initialize with [context]."""
        ...

    def public_method(self, param: str) -> dict | None:
        """What this method does.

        Args:
            param: What this parameter is.

        Returns:
            What gets returned, or None if [condition].

        Raises:
            ValueError: When [condition].
        """
        try:
            result = self._helper(param)
            logger.debug("Method completed", extra={"param": param})
            return result
        except ValueError:
            logger.error("Method failed", extra={"param": param}, exc_info=True)
            raise
        except Exception as e:
            logger.error("Unexpected error", extra={"error": str(e)}, exc_info=True)
            return None

    def _helper(self, param: str) -> dict:
        """Private helper — [what it does]."""
        ...


# ════════════════════════════════════════════════════════════
# Module-level functions (if not class-based)
# ════════════════════════════════════════════════════════════


def standalone_function(arg: str) -> bool:
    """What this function does.

    Args:
        arg: Description.

    Returns:
        True if [condition], False otherwise.
    """
    ...
```

### Python Rules:
- `from __future__ import annotations` at top (PEP 604 unions)
- `logging` setup per module (not root logger)
- Type hints on ALL parameters and return values
- Docstrings on all public functions/classes (Google style)
- `Path` for file operations, never string concatenation
- No bare `except:` — catch specific exceptions
- Use `|` for union types: `str | None` not `Optional[str]`
- Import order: stdlib → third-party → local (enforced by ruff)

---

## Python Test Template

```python
"""Tests for [module_name]."""

import pytest

from [package].[module] import ClassName, standalone_function


# ════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════


@pytest.fixture
def sample_instance():
    """Create a test instance with default config."""
    return ClassName(param="test_value")


@pytest.fixture
def sample_data():
    """Sample input data for tests."""
    return {
        "key": "value",
        "number": 42,
    }


# ════════════════════════════════════════════════════════════
# Unit Tests
# ════════════════════════════════════════════════════════════


class TestClassName:
    """Tests for ClassName."""

    def test_init(self, sample_instance):
        """Verify initialization with valid params."""
        assert sample_instance is not None

    def test_public_method_success(self, sample_instance, sample_data):
        """Verify public_method returns expected result."""
        result = sample_instance.public_method(sample_data["key"])
        assert result is not None
        assert "expected_key" in result

    def test_public_method_invalid_input(self, sample_instance):
        """Verify public_method handles invalid input."""
        with pytest.raises(ValueError):
            sample_instance.public_method("")

    def test_public_method_edge_case(self, sample_instance):
        """Verify behavior with edge case input."""
        result = sample_instance.public_method("edge_case")
        assert result is None  # or whatever the expected behavior is


class TestStandaloneFunction:
    """Tests for standalone_function."""

    @pytest.mark.parametrize("input_val,expected", [
        ("valid", True),
        ("invalid", False),
        ("", False),
    ])
    def test_various_inputs(self, input_val, expected):
        """Verify function with various inputs."""
        assert standalone_function(input_val) == expected
```

### Test Rules:
- One test file per source module: `module.py` → `test_module.py`
- Use `pytest` (not unittest)
- Use fixtures for shared setup
- Use `parametrize` for multiple similar test cases
- Test both success and failure paths
- Test edge cases (empty input, None, max values)
- Tests must be independent — no test depends on another

---

## TypeScript/React Component Template

```tsx
/**
 * [ComponentName] — [One-line description]
 *
 * [Optional: What this component does and where it's used.]
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

// ════════════════════════════════════════════════════════════
// Types
// ════════════════════════════════════════════════════════════

interface ComponentNameProps {
  /** Description of prop */
  data: DataType;
  /** Callback description */
  onAction: (id: string) => void;
  /** Optional prop with default */
  variant?: 'primary' | 'secondary';
}

// ════════════════════════════════════════════════════════════
// Component
// ════════════════════════════════════════════════════════════

export const ComponentName: React.FC<ComponentNameProps> = ({
  data,
  onAction,
  variant = 'primary',
}) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.language === 'fa';

  const [state, setState] = useState<StateType>(initialState);

  useEffect(() => {
    // Setup logic
    return () => {
      // Cleanup
    };
  }, [dependency]);

  const handleClick = (id: string): void => {
    try {
      onAction(id);
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  return (
    <div
      className={`component ${isRTL ? 'rtl' : 'ltr'}`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {/* Component JSX */}
    </div>
  );
};

export default ComponentName;
```

### TypeScript Rules:
- No `any` types — define interfaces for everything
- Props interface above component, exported if shared
- `useTranslation()` in every component that shows text
- RTL awareness: check `i18n.language === 'fa'` and apply `dir` attribute
- Tailwind classes for styling (dark theme defaults)
- Error boundaries for complex components
- `React.FC<Props>` with explicit props interface

---

## React Test Template

```tsx
/**
 * Tests for [ComponentName]
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ComponentName } from '../ComponentName';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'en' },
  }),
}));

describe('ComponentName', () => {
  const defaultProps = {
    data: mockData,
    onAction: vi.fn(),
  };

  it('renders without crashing', () => {
    render(<ComponentName {...defaultProps} />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });

  it('calls onAction when clicked', () => {
    render(<ComponentName {...defaultProps} />);
    fireEvent.click(screen.getByRole('button'));
    expect(defaultProps.onAction).toHaveBeenCalledWith('expected-id');
  });

  it('supports RTL layout', () => {
    vi.mocked(useTranslation).mockReturnValue({
      t: (key: string) => key,
      i18n: { language: 'fa' },
    } as any);

    const { container } = render(<ComponentName {...defaultProps} />);
    expect(container.firstChild).toHaveAttribute('dir', 'rtl');
  });
});
```

---

## Rust Module Template

```rust
//! [Module name] — [One-line description]
//!
//! [Optional: More context about what this module does.]

use std::error::Error;
use log::{info, error, debug};

// ════════════════════════════════════════════════════════════
// Types
// ════════════════════════════════════════════════════════════

/// Brief description of the struct.
///
/// # Examples
///
/// ```
/// let instance = StructName::new(config)?;
/// ```
pub struct StructName {
    config: Config,
}

// ════════════════════════════════════════════════════════════
// Implementation
// ════════════════════════════════════════════════════════════

impl StructName {
    /// Create a new instance.
    ///
    /// # Errors
    ///
    /// Returns error if config is invalid.
    pub fn new(config: Config) -> Result<Self, Box<dyn Error>> {
        info!("StructName initialized");
        Ok(Self { config })
    }

    /// What this method does.
    ///
    /// # Arguments
    ///
    /// * `param` - Description
    ///
    /// # Returns
    ///
    /// Description of return value.
    pub fn method(&self, param: &str) -> Result<Data, Box<dyn Error>> {
        debug!("method called: {}", param);
        let result = self.helper(param)?;
        Ok(result)
    }

    fn helper(&self, param: &str) -> Result<Data, Box<dyn Error>> {
        // Implementation
        todo!()
    }
}

// ════════════════════════════════════════════════════════════
// Tests
// ════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new() {
        let result = StructName::new(Config::default());
        assert!(result.is_ok());
    }

    #[test]
    fn test_method() {
        let instance = StructName::new(Config::default()).unwrap();
        let result = instance.method("test");
        assert!(result.is_ok());
    }
}
```

### Rust Rules:
- `Result<T, E>` everywhere — no `.unwrap()` in production code (ok in tests)
- `cargo clippy -- -D warnings` must pass
- Doc comments with `///` on all public items
- Include `# Examples` in doc comments for public API
- Tests in same file under `#[cfg(test)]` module
- Use `log` crate for logging (not println!)

---

## SQL Migration Template

```sql
-- Migration: [NNN]_[description].sql
-- Date: [YYYY-MM-DD]
-- Description: [What this migration does]

BEGIN;

-- ════════════════════════════════════════════════════════════
-- Changes
-- ════════════════════════════════════════════════════════════

-- [SQL statements here]

-- ════════════════════════════════════════════════════════════
-- Indexes (if adding tables/columns)
-- ════════════════════════════════════════════════════════════

-- [CREATE INDEX statements]

-- ════════════════════════════════════════════════════════════
-- Verification
-- ════════════════════════════════════════════════════════════

-- Quick check that migration worked:
-- SELECT count(*) FROM [new_table];

COMMIT;
```

### SQL Rules:
- Always wrap in `BEGIN; ... COMMIT;`
- Always create a matching rollback file: `[NNN]_[description]_rollback.sql`
- Add indexes for all foreign keys and common query patterns
- Include verification comment showing how to check it worked
