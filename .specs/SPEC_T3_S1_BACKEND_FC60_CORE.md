# SPEC: Backend FC60 Core Engine - T3-S1
**Estimated Duration:** 4-5 hours  
**Layer:** Layer 3 (Backend - Oracle Service)  
**Terminal:** Terminal 3  
**Phase:** Phase 2 (Backend Services)  
**Session:** T3-S1 (FC60 Core Engine Migration + Single-User Reading Service)

---

## ðŸŽ¯ TL;DR

- **Migrating V3 engines:** fc60.py, numerology.py, oracle.py from V3 codebase
- **Creating Oracle reading service:** Single-user FC60 + numerology calculations
- **Python microservice:** FastAPI-based with PostgreSQL integration
- **Comprehensive calculations:** Name, birthday, mother's name, cosmic timing, location
- **Multi-language support:** English + Persian numerology
- **Deliverable:** Production-ready Oracle service with 95%+ test coverage

---

## ðŸ"Œ OBJECTIVE

Create production-ready Oracle service that performs FC60 and numerology calculations for single users, supporting both English and Persian input, with comprehensive cosmic timing and location-based adjustments.

**Success Metric:** User provides (name, birthday, location) → Returns complete FC60 reading with numerology scores, cosmic alignment, and interpretation in <2 seconds.

---

## ðŸ" CONTEXT

### Current State
- V3 monolithic desktop app has working FC60, numerology, and oracle engines
- Engines are in `/nps/engines/` directory (fc60.py, numerology.py, oracle.py)
- Engines are tightly coupled to Tkinter GUI
- No database persistence, calculations done in-memory

### What's Changing
- **Extracting engines** from V3 into standalone Oracle service
- **Adding PostgreSQL persistence** for storing readings and insights
- **Creating FastAPI microservice** for remote access (API Layer 2 will call this)
- **Decoupling from GUI** - pure calculation logic
- **Adding type hints + tests** for production quality

### Why
- Part of V4 distributed architecture (Layer 3 Backend Services)
- Oracle service will analyze Scanner findings for patterns
- Scanner will use Oracle suggestions for targeted key generation
- Need standalone service that can be called via gRPC from API layer

---

## âœ… PREREQUISITES

**Before starting this session, verify:**

- [ ] **Layer 4 (Database) completed**
  - Verification: `psql -h localhost -U nps_user -d nps_db -c "SELECT 1;"`
  - Expected: Connection succeeds, returns 1
  
- [ ] **V3 codebase accessible**
  - Verification: Check if you have access to V3 engines
  - Location: Should have fc60.py, numerology.py, oracle.py files
  
- [ ] **Python 3.11+ installed**
  - Verification: `python3 --version`
  - Expected: Python 3.11.0 or higher
  
- [ ] **PostgreSQL connection string available**
  - Format: `postgresql://nps_user:password@localhost:5432/nps_db`
  - Set in environment: `export DATABASE_URL="..."`

**If any prerequisite fails, STOP and resolve before continuing.**

---

## ðŸ› ï¸ TOOLS TO USE

### Extended Thinking
Use for:
- Architecture decisions (FastAPI vs gRPC for initial service)
- Database schema design for readings storage
- Persian numerology calculation method selection
- Caching strategy for expensive calculations

### Subagents
**Not needed for this session** - We're creating 3-4 files in sequence:
1. Migrate engines (sequential dependency)
2. Create service layer
3. Create tests

Subagents would complicate coordination for this size task.

### Skills
- **NOT APPLICABLE** - This is pure Python backend code, no documents or UI

### MCP Servers
- **Database MCP (if available):** For complex PostgreSQL queries/schema verification
- **File System MCP:** For locating V3 engine files

---

## ðŸ"‹ REQUIREMENTS

### Functional Requirements

**FR1: Engine Migration**
- Migrate fc60.py from V3 with zero calculation changes
- Migrate numerology.py from V3 with zero calculation changes
- Migrate oracle.py from V3 with zero calculation changes
- Remove all GUI dependencies (Tkinter imports, widget references)
- Add type hints to all functions
- Add docstrings to all public methods

**FR2: FC60 Calculations**
- Calculate life path number from birthday (Pythagorean method)
- Calculate destiny number from full name (English + Persian)
- Calculate mother's name influence (energy number)
- FC60 cosmic timing based on current moment
- Location-based adjustments (timezone, latitude, longitude)
- Sign interpretation (time-based, number-based, custom)

**FR3: Single-User Reading Service**
- Accept user input: name, birthday, mother's name, location
- Return comprehensive FC60 reading as structured JSON
- Store reading in PostgreSQL for later retrieval
- Calculate all components in single request (<2s total)

**FR4: Database Integration**
- Store readings in `oracle_readings` table
- Store calculation history for same user
- Query past readings by user_id or session_id
- Support JSONB for flexible reading storage

### Non-Functional Requirements

**NFR1: Performance**
- Single reading calculation: <2s end-to-end
- Pattern analysis (1000 findings): <5s
- Database queries: <100ms
- No blocking operations (async preferred)

**NFR2: Security**
- No plaintext storage of sensitive user data
- Input validation (prevent SQL injection)
- Rate limiting (if exposed via API)

**NFR3: Quality**
- Test coverage: â‰¥95% (per Layer 3 verification checklist)
- Type hints: 100% of functions
- Docstrings: All public functions
- No mypy errors (strict mode)
- JSON logging (structured format)

**NFR4: Maintainability**
- V3 engine compatibility preserved (can swap engines easily)
- Clear separation: engines/ vs services/
- Configuration externalized (config.py)
- Error messages user-friendly

---

## ðŸ" IMPLEMENTATION PLAN

### PHASE 1: V3 Engine Migration (90 minutes)

**Objective:** Extract and adapt V3 engines for standalone use

#### Task 1.1: Create Oracle Service Directory Structure

**Files to create:**
```
backend/oracle-service/
â"œâ"€â"€ app/
â"‚   â"œâ"€â"€ __init__.py
â"‚   â"œâ"€â"€ main.py                # Service entry point (placeholder)
â"‚   â"œâ"€â"€ config.py              # Configuration
â"‚   â"œâ"€â"€ engines/
â"‚   â"‚   â"œâ"€â"€ __init__.py
â"‚   â"‚   â"œâ"€â"€ fc60.py            # Migrated from V3
â"‚   â"‚   â"œâ"€â"€ numerology.py      # Migrated from V3
â"‚   â"‚   â""â"€â"€ oracle.py          # Migrated from V3
â"‚   â"œâ"€â"€ services/
â"‚   â"‚   â"œâ"€â"€ __init__.py
â"‚   â"‚   â""â"€â"€ reading_service.py # To be created in Phase 2
â"‚   â""â"€â"€ database/
â"‚       â"œâ"€â"€ __init__.py
â"‚       â""â"€â"€ connection.py      # PostgreSQL connection
â"œâ"€â"€ tests/
â"‚   â"œâ"€â"€ __init__.py
â"‚   â"œâ"€â"€ test_fc60.py
â"‚   â"œâ"€â"€ test_numerology.py
â"‚   â""â"€â"€ test_reading_service.py
â"œâ"€â"€ requirements.txt
â""â"€â"€ pytest.ini
```

**Acceptance:**
- [ ] Directory structure created
- [ ] All `__init__.py` files present
- [ ] Imports work: `from app.engines import fc60`

**Verification:**
```bash
cd backend/oracle-service
tree app/
# Expected: Structure matches above
python3 -c "from app.engines import fc60" 2>&1 | grep -q "ImportError" && echo "FAIL" || echo "PASS"
```

---

#### Task 1.2: Migrate fc60.py Engine

**Source:** V3 `/nps/engines/fc60.py`  
**Target:** `backend/oracle-service/app/engines/fc60.py`

**Migration Steps:**

1. **Copy base file**
   ```bash
   cp /path/to/v3/nps/engines/fc60.py backend/oracle-service/app/engines/fc60.py
   ```

2. **Remove GUI dependencies**
   - Delete all `import tkinter` statements
   - Delete all widget-related code (Button, Label, Entry, etc.)
   - Remove any GUI callback functions
   - Keep only pure calculation logic

3. **Add type hints**
   ```python
   from typing import Dict, List, Tuple, Optional
   from datetime import datetime, timezone
   
   def calculate_life_path(birthday: datetime) -> int:
       """Calculate Pythagorean life path number."""
       # Implementation
       
   def fc60_encode(value: str) -> str:
       """Encode value into FC60 signature."""
       # Implementation
   ```

4. **Add docstrings**
   - Every public function gets docstring with:
     - Brief description
     - Args with types
     - Returns with type
     - Raises (if any exceptions)
   
   Example:
   ```python
   def calculate_destiny_number(name: str, language: str = "english") -> int:
       """
       Calculate destiny number from full name.
       
       Uses Pythagorean numerology for English names,
       Abjad numerology for Persian names.
       
       Args:
           name: Full name (e.g., "John Doe" or "Ù…Ø­Ù…Ø¯ Ø±Ø¶Ø§")
           language: "english" or "persian"
           
       Returns:
           Single-digit destiny number (1-9)
           
       Raises:
           ValueError: If name is empty or language unsupported
       """
   ```

5. **Add logging**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   def calculate_life_path(birthday: datetime) -> int:
       logger.debug(f"Calculating life path for birthday: {birthday}")
       result = # ... calculation
       logger.debug(f"Life path result: {result}")
       return result
   ```

6. **Configuration externalization**
   - Move any hardcoded values to config.py
   - Persian alphabet mappings → config
   - Calculation constants → config

**Acceptance:**
- [ ] File migrated with zero calculation changes (verified by unit tests)
- [ ] No Tkinter imports
- [ ] Type hints on all functions (mypy --strict passes)
- [ ] Docstrings on all public functions
- [ ] Logging added (JSON format)
- [ ] No hardcoded configuration values

**Verification:**
```bash
cd backend/oracle-service
mypy app/engines/fc60.py --strict
# Expected: Success: no issues found

python3 -c "from app.engines.fc60 import calculate_life_path; print(calculate_life_path.__annotations__)"
# Expected: Shows type hints

grep -c "import tkinter" app/engines/fc60.py
# Expected: 0 (no Tkinter imports)
```

---

#### Task 1.3: Migrate numerology.py Engine

**Source:** V3 `/nps/engines/numerology.py`  
**Target:** `backend/oracle-service/app/engines/numerology.py`

**Follow same process as Task 1.2:**
1. Copy file
2. Remove GUI dependencies
3. Add type hints
4. Add docstrings
5. Add logging
6. Externalize configuration

**Key Functions to Migrate:**
```python
def pythagorean_value(char: str) -> int:
    """Get Pythagorean numerology value for character."""
    
def reduce_to_single_digit(number: int) -> int:
    """Reduce number to single digit (1-9)."""
    
def calculate_name_number(name: str) -> int:
    """Calculate numerology number from name."""
    
def analyze_address(address: str) -> Dict[str, int]:
    """Analyze Bitcoin address numerology patterns."""
```

**Persian Support:**
```python
# Persian alphabet mapping (move to config.py)
PERSIAN_ALPHABET = {
    'Ø§': 1, 'Ø¨': 2, 'Ø¬': 3, 'Ø¯': 4,
    # ... complete mapping
}

def persian_value(char: str) -> int:
    """Get Abjad numerology value for Persian character."""
```

**Acceptance:**
- [ ] Same criteria as fc60.py
- [ ] Persian alphabet support verified
- [ ] Address analysis works on test Bitcoin addresses

**Verification:**
```bash
mypy app/engines/numerology.py --strict
# Expected: Success

python3 -c "from app.engines.numerology import calculate_name_number; print(calculate_name_number('John Doe'))"
# Expected: Valid integer (e.g., 7)
```

---

#### Task 1.4: Migrate oracle.py Engine

**Source:** V3 `/nps/engines/oracle.py`  
**Target:** `backend/oracle-service/app/engines/oracle.py`

**This engine orchestrates fc60.py + numerology.py**

**Key Functions:**
```python
def generate_reading(
    name: str,
    birthday: datetime,
    mother_name: str,
    location: Tuple[float, float],  # (latitude, longitude)
    timezone_str: str
) -> Dict[str, Any]:
    """
    Generate complete FC60 + numerology reading.
    
    Returns comprehensive reading with:
    - Life path number
    - Destiny number
    - Mother's influence
    - FC60 cosmic timing
    - Location adjustments
    - Interpretation text
    """
```

**Acceptance:**
- [ ] Same criteria as previous engines
- [ ] Orchestrates fc60 + numerology correctly
- [ ] Returns structured Dict (not GUI-formatted string)
- [ ] Timezone handling works (uses pytz or zoneinfo)

**Verification:**
```bash
python3 -c "
from app.engines.oracle import generate_reading
from datetime import datetime
result = generate_reading('Test User', datetime(1990, 1, 1), 'Mother', (37.7749, -122.4194), 'America/Los_Angeles')
print(type(result))
print('life_path' in result)
"
# Expected: <class 'dict'>, True
```

---

#### PHASE 1 CHECKPOINT

**Before proceeding to Phase 2, verify:**

- [ ] All 3 engines migrated (fc60, numerology, oracle)
- [ ] Zero Tkinter dependencies
- [ ] Type hints: `mypy app/engines/ --strict` passes
- [ ] No hardcoded config values
- [ ] Logging present in all functions
- [ ] Manual test: Can import and call basic functions

**If checkpoint fails, fix issues before Phase 2.**

**Verification Command:**
```bash
cd backend/oracle-service
mypy app/engines/ --strict && echo "âœ… Type hints OK" || echo "âŒ Type hints FAILED"
python3 -c "from app.engines import fc60, numerology, oracle; print('âœ… Imports OK')"
```

---

### PHASE 2: Reading Service Creation (90 minutes)

**Objective:** Create single-user reading service with PostgreSQL persistence

#### Task 2.1: Create Database Connection Module

**File:** `backend/oracle-service/app/database/connection.py`

**Implementation:**
```python
"""
PostgreSQL connection pool for Oracle service.
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages PostgreSQL connection pool."""
    
    def __init__(self, database_url: str):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string
                         (e.g., postgresql://user:pass@host:5432/db)
        """
        self.database_url = database_url
        self._pool: Optional[Pool] = None
    
    async def connect(self) -> None:
        """Create connection pool."""
        logger.info("Creating PostgreSQL connection pool")
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Connection pool created")
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            logger.info("Closing PostgreSQL connection pool")
            await self._pool.close()
            logger.info("Connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire connection from pool.
        
        Usage:
            async with db.acquire() as conn:
                result = await conn.fetchrow("SELECT 1")
        """
        if not self._pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        async with self._pool.acquire() as connection:
            yield connection
```

**Acceptance:**
- [ ] Connection pool created successfully
- [ ] Acquire context manager works
- [ ] Proper error handling (raises if not connected)
- [ ] Logging present (connection open/close)

**Verification:**
```bash
cd backend/oracle-service
python3 -c "
import asyncio
from app.database.connection import DatabaseConnection
import os

async def test():
    db = DatabaseConnection(os.getenv('DATABASE_URL'))
    await db.connect()
    async with db.acquire() as conn:
        result = await conn.fetchval('SELECT 1')
        print(f'Query result: {result}')
    await db.disconnect()

asyncio.run(test())
"
# Expected: Query result: 1
```

---

#### Task 2.2: Create Configuration Module

**File:** `backend/oracle-service/app/config.py`

**Implementation:**
```python
"""
Oracle service configuration.
"""
import os
from typing import Dict

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nps_user:password@localhost:5432/nps_db"
)

# Persian alphabet numerology mapping (Abjad)
PERSIAN_ALPHABET: Dict[str, int] = {
    'Ø§': 1,  # Alef
    'Ø¨': 2,  # Be
    'Ø¬': 3,  # Jim
    'Ø¯': 4,  # Dal
    'Ù‡': 5,  # He
    'Ùˆ': 6,  # Vav
    'Ø²': 7,  # Ze
    'Ø­': 8,  # He
    'Ø·': 9,  # Ta
    'ÙŠ': 10, # Ya
    # ... complete mapping (get from V3)
}

# English alphabet numerology mapping (Pythagorean)
ENGLISH_ALPHABET: Dict[str, int] = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5,
    'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,
    'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5,
    'X': 6, 'Y': 7, 'Z': 8,
}

# FC60 calculation constants
FC60_CYCLE_DAYS = 60  # FC60 operates on 60-day cycles
FC60_YEAR_START = 1900  # Base year for calculations

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"  # Always JSON for structured logging
```

**Acceptance:**
- [ ] All V3 configuration values extracted
- [ ] Environment variables supported
- [ ] Type hints on all constants
- [ ] Comments explain each configuration group

---

#### Task 2.3: Create Reading Service

**File:** `backend/oracle-service/app/services/reading_service.py`

**Implementation:**
```python
"""
Oracle reading service for single users.

Provides comprehensive FC60 + numerology readings.
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

from app.engines import fc60, numerology, oracle
from app.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

class ReadingService:
    """Generates and stores FC60 readings for users."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize reading service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
    
    async def generate_reading(
        self,
        user_id: str,
        name: str,
        birthday: datetime,
        mother_name: str,
        location: Tuple[float, float],
        timezone_str: str,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive FC60 reading for user.
        
        Args:
            user_id: Unique user identifier
            name: User's full name
            birthday: User's birth date (datetime object)
            mother_name: Mother's name for influence calculation
            location: (latitude, longitude) tuple
            timezone_str: Timezone string (e.g., "America/Los_Angeles")
            language: "english" or "persian" for name numerology
            
        Returns:
            Complete reading as dictionary with:
            {
                "user_id": str,
                "generated_at": datetime,
                "life_path": int,
                "destiny_number": int,
                "mother_influence": int,
                "fc60_signature": str,
                "cosmic_alignment": float,
                "interpretation": str,
                "location_adjustment": Dict,
                "metadata": Dict
            }
            
        Raises:
            ValueError: If input validation fails
        """
        logger.info(f"Generating reading for user: {user_id}")
        
        # Input validation
        if not name or not mother_name:
            raise ValueError("Name and mother's name are required")
        if language not in ["english", "persian"]:
            raise ValueError(f"Unsupported language: {language}")
        
        # Calculate life path from birthday
        life_path = fc60.calculate_life_path(birthday)
        logger.debug(f"Life path: {life_path}")
        
        # Calculate destiny number from name
        destiny_number = numerology.calculate_name_number(name, language)
        logger.debug(f"Destiny number: {destiny_number}")
        
        # Calculate mother's influence
        mother_influence = numerology.calculate_name_number(mother_name, language)
        logger.debug(f"Mother influence: {mother_influence}")
        
        # Get current moment in user's timezone
        user_tz = ZoneInfo(timezone_str)
        now = datetime.now(user_tz)
        
        # Calculate FC60 cosmic timing
        fc60_signature = fc60.fc60_encode(now)
        cosmic_alignment = fc60.calculate_alignment(now, location)
        logger.debug(f"FC60 signature: {fc60_signature}, alignment: {cosmic_alignment}")
        
        # Generate interpretation
        interpretation = oracle.interpret_reading(
            life_path=life_path,
            destiny=destiny_number,
            mother=mother_influence,
            fc60_sign=fc60_signature,
            alignment=cosmic_alignment
        )
        
        # Assemble reading
        reading = {
            "user_id": user_id,
            "generated_at": now,
            "life_path": life_path,
            "destiny_number": destiny_number,
            "mother_influence": mother_influence,
            "fc60_signature": fc60_signature,
            "cosmic_alignment": round(cosmic_alignment, 2),
            "interpretation": interpretation,
            "location_adjustment": {
                "latitude": location[0],
                "longitude": location[1],
                "timezone": timezone_str
            },
            "metadata": {
                "name": name,
                "birthday": birthday.isoformat(),
                "mother_name": mother_name,
                "language": language
            }
        }
        
        # Store in database
        await self._store_reading(reading)
        
        logger.info(f"Reading generated successfully for user: {user_id}")
        return reading
    
    async def _store_reading(self, reading: Dict[str, Any]) -> None:
        """
        Store reading in PostgreSQL.
        
        Args:
            reading: Complete reading dictionary
        """
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO oracle_readings (
                    user_id, generated_at, reading_data
                ) VALUES ($1, $2, $3)
                """,
                reading["user_id"],
                reading["generated_at"],
                reading  # Store entire reading as JSONB
            )
        logger.debug(f"Reading stored for user: {reading['user_id']}")
    
    async def get_user_readings(
        self,
        user_id: str,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Retrieve past readings for user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of readings to return
            
        Returns:
            List of reading dictionaries, newest first
        """
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reading_data
                FROM oracle_readings
                WHERE user_id = $1
                ORDER BY generated_at DESC
                LIMIT $2
                """,
                user_id,
                limit
            )
        
        return [dict(row["reading_data"]) for row in rows]
```

**Acceptance:**
- [ ] Generate reading works end-to-end
- [ ] Input validation present (raises ValueError)
- [ ] Timezone handling correct (uses ZoneInfo)
- [ ] Reading stored in PostgreSQL (JSONB)
- [ ] Retrieve past readings works
- [ ] All calculations called correctly (life path, destiny, etc.)
- [ ] Type hints complete (mypy --strict passes)
- [ ] Docstrings complete
- [ ] Performance: <2s for single reading

**Verification:**
```bash
cd backend/oracle-service
python3 -c "
import asyncio
from datetime import datetime
from app.services.reading_service import ReadingService
from app.database.connection import DatabaseConnection
import os

async def test():
    db = DatabaseConnection(os.getenv('DATABASE_URL'))
    await db.connect()
    
    service = ReadingService(db)
    reading = await service.generate_reading(
        user_id='test_user_1',
        name='John Doe',
        birthday=datetime(1990, 1, 15),
        mother_name='Jane Doe',
        location=(37.7749, -122.4194),  # San Francisco
        timezone_str='America/Los_Angeles'
    )
    
    print(f'Life path: {reading[\"life_path\"]}')
    print(f'Destiny: {reading[\"destiny_number\"]}')
    print(f'FC60: {reading[\"fc60_signature\"]}')
    
    # Retrieve stored reading
    past_readings = await service.get_user_readings('test_user_1')
    print(f'Found {len(past_readings)} past readings')
    
    await db.disconnect()

asyncio.run(test())
"
# Expected: Valid numbers, FC60 signature, 1 past reading found
```

---

#### Task 2.4: Create Main Entry Point

**File:** `backend/oracle-service/app/main.py`

**Implementation:**
```python
"""
Oracle service main entry point.

Provides command-line interface for testing and standalone use.
Later: Will add FastAPI/gRPC server here.
"""
import asyncio
import logging
import sys
from datetime import datetime

from app.config import DATABASE_URL, LOG_LEVEL
from app.database.connection import DatabaseConnection
from app.services.reading_service import ReadingService

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_reading():
    """Test reading generation (for development)."""
    logger.info("Starting Oracle service test")
    
    # Initialize database
    db = DatabaseConnection(DATABASE_URL)
    await db.connect()
    
    try:
        # Create reading service
        service = ReadingService(db)
        
        # Generate test reading
        reading = await service.generate_reading(
            user_id="test_user",
            name="John Doe",
            birthday=datetime(1990, 1, 15),
            mother_name="Jane Smith",
            location=(37.7749, -122.4194),  # San Francisco
            timezone_str="America/Los_Angeles"
        )
        
        # Display results
        print("\n" + "="*60)
        print("FC60 READING")
        print("="*60)
        print(f"User ID: {reading['user_id']}")
        print(f"Generated: {reading['generated_at']}")
        print(f"\nNUMEROLOGY:")
        print(f"  Life Path: {reading['life_path']}")
        print(f"  Destiny: {reading['destiny_number']}")
        print(f"  Mother's Influence: {reading['mother_influence']}")
        print(f"\nFC60:")
        print(f"  Signature: {reading['fc60_signature']}")
        print(f"  Cosmic Alignment: {reading['cosmic_alignment']}%")
        print(f"\nINTERPRETATION:")
        print(f"  {reading['interpretation']}")
        print("="*60 + "\n")
        
        logger.info("Test reading completed successfully")
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_reading())
```

**Acceptance:**
- [ ] Script runs without errors
- [ ] Displays formatted reading
- [ ] Database connection opens and closes cleanly
- [ ] Logging configured (shows INFO level messages)

**Verification:**
```bash
cd backend/oracle-service
export DATABASE_URL="postgresql://nps_user:password@localhost:5432/nps_db"
python3 app/main.py
# Expected: Displays formatted FC60 reading, no errors
```

---

#### PHASE 2 CHECKPOINT

**Before proceeding to Phase 3, verify:**

- [ ] ReadingService generates complete readings
- [ ] Database connection works (pool created)
- [ ] Readings stored in PostgreSQL
- [ ] Past readings retrievable
- [ ] CLI test script works (main.py runs)
- [ ] Performance: <2s per reading
- [ ] Type hints: `mypy app/services/ --strict` passes

**If checkpoint fails, fix issues before Phase 3.**

**Verification:**
```bash
cd backend/oracle-service
mypy app/services/ app/database/ --strict && echo "âœ… Type hints OK" || echo "âŒ Failed"
python3 app/main.py && echo "âœ… CLI test OK" || echo "âŒ Failed"
```

---

### PHASE 3: Testing (90 minutes)

**Objective:** Achieve 95%+ test coverage with comprehensive unit tests

#### Task 3.1: Create Test Infrastructure

**File:** `backend/oracle-service/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=95
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require database)
    slow: Slow tests (>1 second)
```

**File:** `backend/oracle-service/requirements.txt`

```txt
# Core dependencies
asyncpg==0.29.0
pytz==2024.1

# Testing
pytest==8.0.0
pytest-asyncio==0.23.5
pytest-cov==4.1.0
pytest-mock==3.12.0

# Type checking
mypy==1.8.0

# Logging
python-json-logger==2.0.7
```

**Acceptance:**
- [ ] pytest.ini configured correctly
- [ ] requirements.txt has all dependencies
- [ ] Can install: `pip install -r requirements.txt`

**Verification:**
```bash
cd backend/oracle-service
pip install -r requirements.txt
pytest --version
# Expected: pytest 8.0.0 (or similar)
```

---

#### Task 3.2: Create FC60 Engine Tests

**File:** `backend/oracle-service/tests/test_fc60.py`

**Implementation:**
```python
"""
Unit tests for FC60 engine.
"""
import pytest
from datetime import datetime
from app.engines import fc60

class TestFC60Engine:
    """Test FC60 calculations."""
    
    def test_calculate_life_path_basic(self):
        """Test basic life path calculation."""
        # Test case: 1990-01-15 → 1+9+9+0+0+1+1+5 = 26 → 2+6 = 8
        birthday = datetime(1990, 1, 15)
        result = fc60.calculate_life_path(birthday)
        assert result == 8, f"Expected 8, got {result}"
    
    def test_calculate_life_path_master_number(self):
        """Test master number (11, 22, 33) not reduced."""
        # Test case that should result in 11 (don't reduce to 2)
        birthday = datetime(1992, 11, 2)  # 1+9+9+2+1+1+2 = 25 → 2+5 = 7
        # Adjust test based on V3 logic
        result = fc60.calculate_life_path(birthday)
        assert isinstance(result, int)
        assert 1 <= result <= 33
    
    def test_fc60_encode_time(self):
        """Test FC60 time encoding."""
        # Specific time should give consistent FC60 signature
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        result = fc60.fc60_encode(test_time)
        assert isinstance(result, str)
        assert len(result) > 0
        # Signature should include element + animal
        # e.g., "Wood Rat", "Fire Ox", etc.
    
    def test_calculate_alignment(self):
        """Test cosmic alignment calculation."""
        test_time = datetime(2024, 1, 1, 12, 0, 0)
        location = (37.7749, -122.4194)  # San Francisco
        result = fc60.calculate_alignment(test_time, location)
        assert isinstance(result, (int, float))
        assert 0.0 <= result <= 100.0  # Alignment is 0-100%
    
    @pytest.mark.parametrize("birthday,expected", [
        (datetime(2000, 1, 1), 3),  # 2+0+0+0+0+1+0+1 = 4 → 4? Verify from V3
        (datetime(1985, 5, 15), 6), # Verify from V3
    ])
    def test_calculate_life_path_parametrized(self, birthday, expected):
        """Test multiple life path calculations."""
        # NOTE: Replace expected values with actual V3 results
        result = fc60.calculate_life_path(birthday)
        # For now, just verify it returns an int in valid range
        assert isinstance(result, int)
        assert 1 <= result <= 9
```

**Important:** Get actual test cases from V3 by running calculations there and recording results.

**Acceptance:**
- [ ] All tests pass
- [ ] Coverage >95% of fc60.py
- [ ] Test master numbers (11, 22, 33) if V3 supports
- [ ] Test edge cases (leap years, etc.)

---

#### Task 3.3: Create Numerology Engine Tests

**File:** `backend/oracle-service/tests/test_numerology.py`

```python
"""
Unit tests for numerology engine.
"""
import pytest
from app.engines import numerology

class TestNumerologyEngine:
    """Test numerology calculations."""
    
    def test_pythagorean_value_basic(self):
        """Test basic Pythagorean values."""
        assert numerology.pythagorean_value('A') == 1
        assert numerology.pythagorean_value('B') == 2
        assert numerology.pythagorean_value('I') == 9
        assert numerology.pythagorean_value('J') == 1  # Wraps around
    
    def test_calculate_name_number_english(self):
        """Test English name numerology."""
        # "JOHN" = J(1) + O(6) + H(8) + N(5) = 20 → 2+0 = 2
        result = numerology.calculate_name_number("JOHN", "english")
        assert result == 2
        
        # "DOE" = D(4) + O(6) + E(5) = 15 → 1+5 = 6
        result = numerology.calculate_name_number("DOE", "english")
        assert result == 6
    
    def test_calculate_name_number_persian(self):
        """Test Persian name numerology."""
        # Use actual Persian name from V3 tests
        # e.g., "Ù…Ø­Ù…Ø¯" with known result
        # result = numerology.calculate_name_number("Ù…Ø­Ù…Ø¯", "persian")
        # assert result == <expected from V3>
        pass  # TODO: Get Persian test cases from V3
    
    def test_reduce_to_single_digit(self):
        """Test number reduction."""
        assert numerology.reduce_to_single_digit(26) == 8  # 2+6
        assert numerology.reduce_to_single_digit(100) == 1 # 1+0+0
        assert numerology.reduce_to_single_digit(5) == 5   # Already single
    
    def test_analyze_address(self):
        """Test Bitcoin address analysis."""
        # Use real Bitcoin address
        address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block
        result = numerology.analyze_address(address)
        assert isinstance(result, dict)
        assert "score" in result
        assert isinstance(result["score"], int)
```

**Acceptance:**
- [ ] All tests pass
- [ ] Coverage >95% of numerology.py
- [ ] Both English and Persian tested
- [ ] Address analysis tested with real Bitcoin addresses

---

#### Task 3.4: Create Reading Service Integration Tests

**File:** `backend/oracle-service/tests/test_reading_service.py`

```python
"""
Integration tests for reading service.

Requires PostgreSQL database.
"""
import pytest
import asyncio
from datetime import datetime
from app.services.reading_service import ReadingService
from app.database.connection import DatabaseConnection
import os

# Mark all tests as integration (require database)
pytestmark = pytest.mark.integration

@pytest.fixture
async def db_connection():
    """Provide database connection for tests."""
    db_url = os.getenv("DATABASE_URL", "postgresql://nps_user:password@localhost:5432/nps_db")
    db = DatabaseConnection(db_url)
    await db.connect()
    yield db
    await db.disconnect()

@pytest.fixture
async def reading_service(db_connection):
    """Provide reading service instance."""
    return ReadingService(db_connection)

class TestReadingService:
    """Test reading service end-to-end."""
    
    @pytest.mark.asyncio
    async def test_generate_reading_basic(self, reading_service):
        """Test basic reading generation."""
        reading = await reading_service.generate_reading(
            user_id="test_user_1",
            name="John Doe",
            birthday=datetime(1990, 1, 15),
            mother_name="Jane Doe",
            location=(37.7749, -122.4194),
            timezone_str="America/Los_Angeles"
        )
        
        # Verify structure
        assert reading["user_id"] == "test_user_1"
        assert "life_path" in reading
        assert "destiny_number" in reading
        assert "mother_influence" in reading
        assert "fc60_signature" in reading
        assert "cosmic_alignment" in reading
        assert "interpretation" in reading
        
        # Verify data types
        assert isinstance(reading["life_path"], int)
        assert 1 <= reading["life_path"] <= 9
        assert isinstance(reading["cosmic_alignment"], (int, float))
        assert 0 <= reading["cosmic_alignment"] <= 100
    
    @pytest.mark.asyncio
    async def test_generate_reading_persian(self, reading_service):
        """Test Persian name support."""
        reading = await reading_service.generate_reading(
            user_id="test_user_2",
            name="Ù…Ø­Ù…Ø¯",  # Persian name
            birthday=datetime(1985, 5, 20),
            mother_name="ÙØ§Ø·Ù…Ù‡",  # Persian name
            location=(35.6892, 51.3890),  # Tehran
            timezone_str="Asia/Tehran",
            language="persian"
        )
        
        assert reading["user_id"] == "test_user_2"
        assert "destiny_number" in reading
        # Persian alphabet should work differently than English
    
    @pytest.mark.asyncio
    async def test_get_user_readings(self, reading_service):
        """Test retrieving past readings."""
        user_id = "test_user_history"
        
        # Generate 3 readings
        for i in range(3):
            await reading_service.generate_reading(
                user_id=user_id,
                name=f"User {i}",
                birthday=datetime(1990, 1, i+1),
                mother_name="Mother",
                location=(0, 0),
                timezone_str="UTC"
            )
        
        # Retrieve readings
        readings = await reading_service.get_user_readings(user_id, limit=10)
        assert len(readings) >= 3
        
        # Verify newest first
        for i in range(len(readings) - 1):
            assert readings[i]["generated_at"] >= readings[i+1]["generated_at"]
    
    @pytest.mark.asyncio
    async def test_input_validation(self, reading_service):
        """Test input validation raises errors."""
        with pytest.raises(ValueError, match="Name and mother's name are required"):
            await reading_service.generate_reading(
                user_id="test",
                name="",  # Empty name
                birthday=datetime(1990, 1, 1),
                mother_name="Mother",
                location=(0, 0),
                timezone_str="UTC"
            )
        
        with pytest.raises(ValueError, match="Unsupported language"):
            await reading_service.generate_reading(
                user_id="test",
                name="User",
                birthday=datetime(1990, 1, 1),
                mother_name="Mother",
                location=(0, 0),
                timezone_str="UTC",
                language="invalid"  # Invalid language
            )
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_performance_single_reading(self, reading_service):
        """Test reading generation performance."""
        import time
        start = time.time()
        
        await reading_service.generate_reading(
            user_id="perf_test",
            name="Performance Test",
            birthday=datetime(1990, 1, 1),
            mother_name="Mother",
            location=(0, 0),
            timezone_str="UTC"
        )
        
        duration = time.time() - start
        assert duration < 2.0, f"Reading took {duration}s, expected <2s"
```

**Acceptance:**
- [ ] All integration tests pass
- [ ] Database connection works
- [ ] Readings stored and retrieved correctly
- [ ] Persian language support verified
- [ ] Input validation tested (raises ValueError)
- [ ] Performance test passes (<2s)

---

#### PHASE 3 CHECKPOINT

**Before considering this session complete, verify:**

- [ ] **Test coverage â‰¥95%**
  ```bash
  pytest --cov=app --cov-report=term-missing
  # Expected: Coverage >= 95%
  ```

- [ ] **All tests pass**
  ```bash
  pytest tests/ -v
  # Expected: All tests PASSED
  ```

- [ ] **Type checking passes**
  ```bash
  mypy app/ --strict
  # Expected: Success: no issues found
  ```

- [ ] **Integration tests work**
  ```bash
  pytest tests/test_reading_service.py -v -m integration
  # Expected: All integration tests PASSED
  ```

**If checkpoint fails, fix issues before declaring session complete.**

---

## âœ… SUCCESS CRITERIA

**This session is complete when ALL of these are verified:**

### Code Quality
- [ ] Type hints: 100% of functions (`mypy app/ --strict` passes)
- [ ] Docstrings: All public functions documented
- [ ] Logging: JSON format, all operations logged
- [ ] Error handling: Explicit (no bare except)
- [ ] No hardcoded values (use config.py)

### Functionality
- [ ] FC60 engine works (migrated from V3 with zero calculation changes)
- [ ] Numerology engine works (English + Persian)
- [ ] Oracle readings generate correctly
- [ ] Database storage works (PostgreSQL JSONB)
- [ ] Past readings retrieval works

### Performance
- [ ] Single reading: <2s end-to-end
- [ ] Database queries: <100ms
- [ ] No blocking operations (async where appropriate)

### Testing
- [ ] Test coverage: â‰¥95%
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Edge cases covered (empty input, invalid language, etc.)

### Architecture Alignment
- [ ] Follows Layer 3 Backend structure (from architecture plan)
- [ ] Engines separated from services
- [ ] Database layer abstracted (connection.py)
- [ ] Configuration externalized (config.py)
- [ ] No GUI dependencies (zero Tkinter imports)

---

## ðŸ"Š VERIFICATION CHECKLIST (2-Minute Check)

### Terminal 1: Type Checking + Tests
```bash
cd backend/oracle-service

# 1. Type checking
mypy app/ --strict
# Expected: Success: no issues found

# 2. Run all tests
pytest tests/ -v --cov=app --cov-report=term-missing
# Expected: All tests PASSED, coverage >= 95%

# 3. Integration tests specifically
pytest tests/test_reading_service.py -v -m integration
# Expected: All integration tests PASSED
```

### Terminal 2: Manual Functionality Test
```bash
cd backend/oracle-service
export DATABASE_URL="postgresql://nps_user:password@localhost:5432/nps_db"

# Run CLI test
python3 app/main.py
# Expected: Displays formatted FC60 reading, no errors

# Verify database storage
psql -h localhost -U nps_user -d nps_db -c "SELECT COUNT(*) FROM oracle_readings;"
# Expected: At least 1 row
```

### Visual/Manual Check
- [ ] Reading displays all components (life path, destiny, FC60, interpretation)
- [ ] No error messages or warnings
- [ ] Logs show JSON format
- [ ] Reading stored in database (verified with psql query)

---

## ðŸš€ NEXT 3 ACTIONS (After This Session)

### Action 1: Create FastAPI/gRPC Server (T3-S2)
**Context:** Oracle service currently has CLI only. Need API endpoint for Layer 2 to call.

**Task:** Add FastAPI server to `app/main.py` with:
- `POST /reading` endpoint accepting user data
- Returns FC60 reading as JSON
- gRPC server alternative (for Scanner service communication)

**Estimated Time:** 2 hours

**Verification:**
```bash
curl -X POST http://localhost:8001/reading \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "birthday": "1990-01-15", ...}'
# Expected: Returns complete reading JSON
```

---

### Action 2: Create Pattern Analysis Service (T3-S3)
**Context:** Scanner needs Oracle to analyze vault findings and suggest lucky ranges.

**Task:** Create `app/services/pattern_service.py` with:
- Function: `analyze_findings(findings: List[Finding]) -> RangeSuggestion`
- Analyzes numerology patterns in successful wallet addresses
- Returns weighted range suggestion for Scanner

**Estimated Time:** 3 hours

**Verification:**
```bash
python3 -c "
from app.services.pattern_service import analyze_findings
# Mock findings with balance > 0
suggestion = analyze_findings(mock_findings)
print(f'Suggested range: {suggestion.range_start} - {suggestion.range_end}')
print(f'Confidence: {suggestion.weight}')
"
# Expected: Valid range suggestion with reasoning
```

---

### Action 3: Create AI Integration (T3-S4)
**Context:** Oracle needs Claude API to find correlations between patterns and success.

**Task:** Create `app/engines/ai_engine.py` with:
- Claude CLI integration
- Function: `find_correlations(patterns: Dict) -> AIInsight`
- Uses extended thinking for pattern analysis
- Returns AI-generated insights and recommendations

**Estimated Time:** 2-3 hours

**Verification:**
```bash
python3 -c "
from app.engines.ai_engine import find_correlations
insight = find_correlations({'pattern1': 0.8, 'pattern2': 0.6})
print(f'AI insight: {insight.explanation}')
print(f'Confidence: {insight.confidence}')
"
# Expected: AI-generated analysis with confidence score
```

---

## ðŸ" HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

### Resume from Phase: [Current Phase Number]

**Context Needed:**
- V3 engine files location: `/path/to/v3/nps/engines/`
- Database connection string: `$DATABASE_URL`
- Which engines migrated so far: [List]
- Which tests written so far: [List]

### Verification Before Continuing:

**Check Phase 1 Completion:**
```bash
cd backend/oracle-service
python3 -c "from app.engines import fc60, numerology, oracle; print('âœ… Engines imported')"
mypy app/engines/ --strict && echo "âœ… Type hints OK"
```

**Check Phase 2 Completion:**
```bash
python3 app/main.py && echo "âœ… Reading service works"
```

**Check Phase 3 Completion:**
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
# Expected: >= 95% coverage, all tests pass
```

---

## âš ï¸ KNOWN ISSUES & GOTCHAS

### Issue 1: Persian Alphabet Mapping Incomplete
**Symptom:** Persian names fail with KeyError  
**Cause:** Not all Persian letters in PERSIAN_ALPHABET dict  
**Fix:** Complete mapping in config.py from V3  
**Workaround:** Use English names only for testing

### Issue 2: Timezone Data Missing
**Symptom:** `ZoneInfo("America/Los_Angeles")` raises error  
**Cause:** `tzdata` package not installed  
**Fix:** `pip install tzdata`  
**Prevention:** Add to requirements.txt

### Issue 3: Database Schema Not Created
**Symptom:** `INSERT INTO oracle_readings` fails with "table does not exist"  
**Cause:** Layer 4 (Database) not completed  
**Fix:** Run database migration:
```bash
psql -h localhost -U nps_user -d nps_db -f /path/to/database/migrations/002_oracle_tables.sql
```

### Issue 4: V3 Engine Calculation Differences
**Symptom:** Tests fail because results differ from V3  
**Cause:** Refactoring changed calculation logic  
**Fix:** Run side-by-side comparison:
```python
# In V3:
result_v3 = fc60.calculate_life_path(datetime(1990, 1, 15))

# In V4:
result_v4 = fc60.calculate_life_path(datetime(1990, 1, 15))

assert result_v3 == result_v4  # Must match exactly
```

---

## ðŸ"š REFERENCES

### Internal Documents
- Architecture Plan: `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` (Layer 3B Oracle Service)
- Verification Checklist: `/mnt/project/VERIFICATION_CHECKLISTS.md` (Oracle Service section)
- Tool Orchestration: `/mnt/project/TOOL_ORCHESTRATION_MATRIX.md` (Layer 3 workflows)

### External Resources
- asyncpg documentation: https://magicstack.github.io/asyncpg/
- Python async best practices: https://docs.python.org/3/library/asyncio.html
- FC60 numerology: (V3 documentation if available)

### V3 Codebase
- FC60 engine: `/nps/engines/fc60.py`
- Numerology engine: `/nps/engines/numerology.py`
- Oracle engine: `/nps/engines/oracle.py`

---

## ðŸ'¬ NOTES FOR SESSION EXECUTOR

### Context to Remember

"The Oracle service is the 'brain' of NPS V4. It takes user input (name, birthday, location) and generates comprehensive numerological readings using FC60 cosmic timing. Later sessions will extend this to analyze Scanner findings and suggest 'lucky' private key ranges based on numerology patterns. The hypothesis is that certain numerology patterns correlate with successful wallet discoveries."

### Critical Decisions Made

1. **Database Storage:** Store entire reading as JSONB for flexibility (not normalized tables)
   - Pro: Easy to evolve reading structure without migrations
   - Con: Harder to query individual fields
   - Rationale: Reading structure will evolve as we learn, JSONB allows schema flexibility

2. **Async Architecture:** Use asyncpg and async/await throughout
   - Pro: Non-blocking database I/O
   - Con: More complex than sync code
   - Rationale: Critical for performance when analyzing 1000+ findings

3. **Engine Migration Strategy:** Copy-paste from V3, minimal changes
   - Pro: Preserves tested calculation logic
   - Con: May have V3 architectural debt
   - Rationale: Calculations are complex and fragile, don't fix what isn't broken

### Questions to Explore

1. **Should FC60 calculations be cached?**
   - Current: Recalculate every time
   - Alternative: Cache results by (name, birthday, location)
   - Consider: Trade-off between memory and CPU

2. **How to handle conflicting timezone data?**
   - Example: User says "Los Angeles" but coordinates are in New York
   - Current: Trust timezone string
   - Alternative: Derive timezone from coordinates

---

## âœ… QUALITY SCORE CARD

Use this to grade deliverable before declaring complete:

| Category | Weight | Target | Score (0-100) |
|----------|--------|--------|---------------|
| **Code Quality** | 20% | Type hints, docstrings, logging | ___/100 |
| **Testing** | 25% | 95%+ coverage, all tests pass | ___/100 |
| **Functionality** | 20% | All engines work, readings generate | ___/100 |
| **Architecture** | 15% | Follows Layer 3 structure | ___/100 |
| **Performance** | 10% | <2s readings, <100ms queries | ___/100 |
| **Documentation** | 10% | Docstrings, comments, README | ___/100 |
| **TOTAL** | 100% | **Passing Grade: â‰¥90/100** | **___/100** |

**Swiss Watch Grade: â‰¥95/100** ðŸ†

---

## ðŸ"„ VERSION HISTORY

- **v1.0** (2026-02-08): Initial specification for T3-S1 FC60 Core Engine migration
- **Author:** Generated from NPS V4 Architecture Plan + Verification Checklists
- **Status:** Ready for Claude Code CLI execution

---

**END OF SPECIFICATION**

*Remember: This is a living document. If you discover better approaches during implementation, document them and update the spec.*

*The goal is production-ready code with Swiss watch precision - not just "working" code.* ðŸš€
