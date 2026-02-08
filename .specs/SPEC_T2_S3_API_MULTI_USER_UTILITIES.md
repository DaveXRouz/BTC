# SPEC: API Multi-User + Utilities - T2-S3
**Estimated Duration:** 3-4 hours  
**Layer:** Layer 2 (API)  
**Terminal:** Terminal 2  
**Phase:** Phase 1 (Foundation) - Extended Features  
**Session:** T2-S3

---

## TL;DR

- Creating 3 new API endpoint groups: Multi-user readings, Translation service, Location services
- Multi-user readings: Coordinates with Terminal 3 (FC60 multi-user service) for relationship readings
- Translation: Claude API integration for English ↔ Persian high-quality translation with caching
- Location: IP geolocation + city lookup with timezone support
- All endpoints: Full auth, caching, database storage, 95%+ test coverage
- Performance: <100ms p95 (translation may be slower due to AI)
- Estimated: 200+ lines of new code, 150+ lines of tests

---

## OBJECTIVE

Create production-ready API endpoints that extend NPS V4 Oracle service with multi-user relationship readings, real-time translation capabilities, and location intelligence for personalized astrological insights.

---

## CONTEXT

**Current State:**
- Terminal 2 (API Layer) has basic Oracle endpoints (single-user readings)
- Terminal 3 (Oracle Service) has multi-user FC60 capability (completed in T3-S2)
- Terminal 4 (Database) has junction table for multi-user readings
- No translation or location services exist yet

**What's Changing:**
This spec adds:
1. **Multi-User Reading Endpoint** - Enables relationship/compatibility readings between multiple users
2. **Translation Service** - Bidirectional English ↔ Persian translation for global accessibility
3. **Location Services** - Geographic coordinate lookup and IP-based detection for timezone/location context

**Why:**
- **Multi-User:** Oracle service can analyze relationships (couples, business partners, family) but lacks API exposure
- **Translation:** Users speak Persian/English, need seamless translation for readings and questions
- **Location:** FC60 calculations require accurate timezone/coordinates for birth charts and cosmic timing

**Architecture Alignment:**
- Follows Layer 2 (API) → Layer 3 (Oracle Service) → Layer 4 (Database) pattern
- Uses Claude API (product-self-knowledge skill) for translation
- Caching strategy reduces external API calls and database queries
- All endpoints secured with API key authentication

---

## PREREQUISITES

**Completed Dependencies:**
- [x] Terminal 3 Session 2: Multi-user FC60 service operational
- [x] Terminal 4: Junction table `reading_participants` exists
- [x] Terminal 2 Session 1: Base API infrastructure + auth middleware
- [x] Claude API key available in environment (NPS_ANTHROPIC_API_KEY)

**Verification Commands:**
```bash
# Check T3 multi-user service
curl http://oracle:50052/health
# Expected: {"status": "healthy"}

# Check database table
psql -c "\d reading_participants"
# Expected: Table structure visible

# Check API auth
curl -H "Authorization: Bearer test_key" http://localhost:8000/api/health
# Expected: 200 OK

# Check Claude API key
printenv | grep NPS_ANTHROPIC_API_KEY
# Expected: Key present
```

**Environment Setup:**
```bash
cd api
source venv/bin/activate
pip list | grep -E "anthropic|redis|geopy"
# If missing, install:
pip install anthropic==0.18.1 redis==5.0.1 geopy==2.4.1 --break-system-packages
```

---

## TOOLS TO USE

**Extended Thinking:**
- Translation caching strategy (Redis vs in-memory vs database)
- Location API selection (free tier limits, accuracy trade-offs)
- Multi-user reading storage pattern (junction table optimization)

**Subagents:**
- Subagent 1: Multi-user reading endpoint + models
- Subagent 2: Translation endpoint + caching
- Subagent 3: Location endpoints (coordinates + IP detect)
- Subagent 4: Comprehensive tests for all endpoints

**MCP Servers:**
- Database MCP: Junction table queries
- (Optional) Redis MCP: Caching if using Redis

**Skills:**
- product-self-knowledge: Claude API integration patterns
- (Reference) NPS_V4_ARCHITECTURE_PLAN.md Layer 2 section

---

## REQUIREMENTS

### Functional Requirements

**FR1: Multi-User Reading Endpoint**
- Accept POST request with primary user + multiple secondary users
- Validate: All user_ids exist in database (users table)
- Call Terminal 3 multi-user FC60 service via gRPC
- Store reading with participants in junction table
- Return combined analysis (primary compatibility with each secondary)
- Support question with sign_type/sign_value for specific queries

**FR2: Translation Service**
- Bidirectional translation: English ↔ Persian (Farsi)
- Use Claude API with streaming for long texts
- Cache translations to avoid re-translating identical texts
- Preserve formatting (line breaks, bullet points)
- Handle technical terminology (FC60, numerology terms)
- Return both translated + original text

**FR3: Location Coordinates Endpoint**
- Accept city name + country code
- Return: {latitude, longitude, timezone, city_display_name}
- Cache common cities (Tehran, London, New York, etc.)
- Use free geocoding API (Nominatim OpenStreetMap)
- Rate limit: 1 request/second to respect Nominatim policy

**FR4: Location IP Detection Endpoint**
- Detect user's location from IP address
- Return: {latitude, longitude, timezone, city, country}
- Use ipapi.co (free tier: 1000 requests/day)
- Cache IP → location mapping (IPs don't change location frequently)
- Fallback to default location if IP detection fails

### Non-Functional Requirements

**NFR1: Performance**
- Multi-user reading: <200ms p95 (depends on T3 service)
- Translation: <3s for <500 words (Claude API latency)
- Location lookup: <100ms (cached), <500ms (uncached)
- IP detection: <200ms (cached), <1s (uncached with external API)

**NFR2: Security**
- All endpoints require API key authentication
- User IDs validated against authenticated user (can't read other users' private data without permission)
- Claude API key stored in environment variable (not hardcoded)
- External API keys (ipapi.co) in environment

**NFR3: Quality**
- Test coverage: 95%+ for all new endpoints
- Translation accuracy: Manually verified for 10+ sample phrases
- Location accuracy: ±10km for major cities
- Error messages in English (primary) with optional Persian translation

**NFR4: Scalability**
- Translation cache: LRU with max 1000 entries (in-memory for simplicity)
- Location cache: 500 cities + 1000 IPs (in-memory)
- Database: Indexed user_id in junction table for fast lookups
- Rate limiting: 100 requests/minute per API key for translation

---

## IMPLEMENTATION PLAN

### Phase 1: Multi-User Reading Endpoint (90 min)

**Extended Thinking Decision: Storage Pattern**
<thinking>
DECISION: How to store multi-user readings with participants?

OPTIONS:
1. **Flat JSON in readings table**
   - Pros: Simple, one table
   - Cons: Can't query "all readings user X participated in", no referential integrity
   
2. **Junction table (reading_participants)**
   - Pros: Relational integrity, queryable, normalized
   - Cons: Additional table, more complex queries
   
3. **Array column in readings**
   - Pros: PostgreSQL array support, one table
   - Cons: Limited querying, no foreign keys

EVALUATION:
- Need to query: "All readings where user X was involved" (for history)
- Need referential integrity (user_id must exist)
- Multi-user readings are core feature (not edge case)

RECOMMENDATION: Junction table (Option 2)
- Already designed in Terminal 4
- Best for relational queries
- Scalable for future features (permissions, sharing)
</thinking>

**Tasks:**

**1.1: Pydantic Models (20 min)**

Create `api/app/models/oracle.py` additions:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class MultiUserReadingRequest(BaseModel):
    """Request model for multi-user FC60 reading."""
    
    primary_user_id: int = Field(..., description="Primary user ID (reference point)")
    secondary_user_ids: List[int] = Field(..., min_items=1, max_items=5, description="Other users (1-5)")
    question: Optional[str] = Field(None, max_length=500, description="Optional specific question")
    sign_type: str = Field(..., description="FC60 sign type: birth_date, birth_time, question_time, name")
    sign_value: str = Field(..., description="Value for sign type (date, time, or name)")
    
    @validator('secondary_user_ids')
    def no_duplicate_users(cls, v, values):
        """Ensure no duplicate user IDs."""
        if 'primary_user_id' in values and values['primary_user_id'] in v:
            raise ValueError("Primary user cannot be in secondary users list")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs in secondary users")
        return v

class MultiUserReadingResponse(BaseModel):
    """Response model for multi-user reading."""
    
    reading_id: int
    primary_user: dict  # {id, name, sign}
    secondary_users: List[dict]  # [{id, name, sign, compatibility}, ...]
    combined_analysis: str
    question: Optional[str]
    created_at: datetime
    fc60_details: dict  # Full FC60 calculation results

class UserParticipant(BaseModel):
    """Participant in multi-user reading."""
    
    user_id: int
    name: str
    fc60_sign: str
    role: str  # "primary" or "secondary"
    compatibility_score: Optional[float] = None  # Only for secondary users
```

**Acceptance:**
- [ ] Models defined with proper validation
- [ ] Type hints complete
- [ ] Docstrings added
- [ ] mypy --strict passes

**Verification:**
```bash
cd api
python -c "from app.models.oracle import MultiUserReadingRequest; print('Models loaded')"
# Expected: "Models loaded"
mypy app/models/oracle.py --strict
# Expected: Success: no issues found
```

---

**1.2: Oracle Service Client (30 min)**

Create `api/app/services/oracle_service.py` (new file):

```python
import grpc
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Import gRPC generated code (from Terminal 3)
from shared.proto import oracle_pb2, oracle_pb2_grpc

logger = logging.getLogger(__name__)

class OracleServiceClient:
    """Client for Terminal 3 Oracle service via gRPC."""
    
    def __init__(self, oracle_url: str = "oracle:50052"):
        self.oracle_url = oracle_url
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Establish gRPC connection."""
        self.channel = grpc.insecure_channel(self.oracle_url)
        self.stub = oracle_pb2_grpc.OracleServiceStub(self.channel)
        logger.info(f"Connected to Oracle service at {self.oracle_url}")
    
    def close(self):
        """Close gRPC connection."""
        if self.channel:
            self.channel.close()
    
    async def multi_user_reading(
        self,
        primary_user: Dict,
        secondary_users: List[Dict],
        question: Optional[str],
        sign_type: str,
        sign_value: str
    ) -> Dict:
        """
        Request multi-user FC60 reading.
        
        Args:
            primary_user: {id, name, birth_date}
            secondary_users: [{id, name, birth_date}, ...]
            question: Optional question text
            sign_type: Type of sign calculation
            sign_value: Value for sign
            
        Returns:
            {
                "primary": {...},
                "secondary": [{...}, ...],
                "combined_analysis": "...",
                "fc60_details": {...}
            }
        """
        if not self.stub:
            self.connect()
        
        try:
            # Build gRPC request
            request = oracle_pb2.MultiUserReadingRequest(
                primary_user=oracle_pb2.User(
                    id=primary_user['id'],
                    name=primary_user['name'],
                    birth_date=primary_user.get('birth_date', '')
                ),
                secondary_users=[
                    oracle_pb2.User(
                        id=u['id'],
                        name=u['name'],
                        birth_date=u.get('birth_date', '')
                    )
                    for u in secondary_users
                ],
                question=question or "",
                sign_type=sign_type,
                sign_value=sign_value
            )
            
            # Call Oracle service
            response = self.stub.GetMultiUserReading(request, timeout=10.0)
            
            # Parse response
            result = {
                "primary": {
                    "id": primary_user['id'],
                    "name": primary_user['name'],
                    "fc60_sign": response.primary_sign,
                    "element": response.primary_element
                },
                "secondary": [
                    {
                        "id": secondary_users[i]['id'],
                        "name": secondary_users[i]['name'],
                        "fc60_sign": sec.sign,
                        "element": sec.element,
                        "compatibility_score": sec.compatibility
                    }
                    for i, sec in enumerate(response.secondary_users)
                ],
                "combined_analysis": response.analysis,
                "fc60_details": {
                    "primary_full": response.primary_details,
                    "relationships": response.relationship_dynamics
                }
            }
            
            logger.info(f"Multi-user reading completed for primary user {primary_user['id']}")
            return result
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error: {e.code()} - {e.details()}")
            raise Exception(f"Oracle service unavailable: {e.details()}")
        except Exception as e:
            logger.error(f"Multi-user reading failed: {str(e)}", exc_info=True)
            raise

# Singleton instance
oracle_client = OracleServiceClient()
```

**Acceptance:**
- [ ] gRPC client implements multi-user reading call
- [ ] Error handling for service unavailable
- [ ] Logging at appropriate levels
- [ ] Type hints complete

**Verification:**
```bash
# Mock test (Terminal 3 service must be running)
python -c "
from app.services.oracle_service import oracle_client
oracle_client.connect()
print('Oracle client connected')
oracle_client.close()
"
# Expected: "Oracle client connected"
```

---

**1.3: Multi-User Reading Endpoint (40 min)**

Add to `api/app/routers/oracle.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.oracle import MultiUserReadingRequest, MultiUserReadingResponse
from app.services.oracle_service import oracle_client
from app.security.auth import validate_api_key

router = APIRouter()

@router.post("/reading/multi-user", response_model=MultiUserReadingResponse)
async def create_multi_user_reading(
    request: MultiUserReadingRequest,
    db: Session = Depends(get_db),
    auth: dict = Depends(validate_api_key)
):
    """
    Create multi-user FC60 reading for relationship compatibility.
    
    Analyzes compatibility between primary user and multiple secondary users.
    Useful for: couples, business partnerships, family dynamics, team compatibility.
    
    **Scope required:** oracle_read
    
    **Example:**
    ```json
    {
      "primary_user_id": 1,
      "secondary_user_ids": [2, 3],
      "question": "What is our team dynamic?",
      "sign_type": "birth_date",
      "sign_value": "1990-01-15"
    }
    ```
    
    **Response:**
    - reading_id: Unique reading ID
    - primary_user: Primary user details + FC60 sign
    - secondary_users: List of secondary users with compatibility scores
    - combined_analysis: Overall relationship dynamics
    - fc60_details: Detailed FC60 calculations
    """
    
    # Validate user IDs exist
    all_user_ids = [request.primary_user_id] + request.secondary_user_ids
    users = db.query(User).filter(User.id.in_(all_user_ids)).all()
    
    if len(users) != len(all_user_ids):
        missing = set(all_user_ids) - {u.id for u in users}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Users not found: {missing}"
        )
    
    # Build user dicts for Oracle service
    user_dict = {u.id: u for u in users}
    
    primary = {
        "id": request.primary_user_id,
        "name": user_dict[request.primary_user_id].name,
        "birth_date": user_dict[request.primary_user_id].birth_date.isoformat() if user_dict[request.primary_user_id].birth_date else None
    }
    
    secondaries = [
        {
            "id": uid,
            "name": user_dict[uid].name,
            "birth_date": user_dict[uid].birth_date.isoformat() if user_dict[uid].birth_date else None
        }
        for uid in request.secondary_user_ids
    ]
    
    # Call Oracle service
    try:
        result = await oracle_client.multi_user_reading(
            primary_user=primary,
            secondary_users=secondaries,
            question=request.question,
            sign_type=request.sign_type,
            sign_value=request.sign_value
        )
    except Exception as e:
        logger.error(f"Oracle service call failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Oracle service temporarily unavailable"
        )
    
    # Store reading in database
    from app.database.models import Reading, ReadingParticipant
    
    reading = Reading(
        user_id=request.primary_user_id,
        reading_type="multi_user",
        question=request.question,
        sign_type=request.sign_type,
        sign_value=request.sign_value,
        result=result['combined_analysis'],
        fc60_data=result['fc60_details']
    )
    db.add(reading)
    db.flush()  # Get reading.id
    
    # Store participants
    participants = [
        ReadingParticipant(
            reading_id=reading.id,
            user_id=request.primary_user_id,
            role="primary",
            fc60_sign=result['primary']['fc60_sign']
        )
    ]
    
    for sec in result['secondary']:
        participants.append(
            ReadingParticipant(
                reading_id=reading.id,
                user_id=sec['id'],
                role="secondary",
                fc60_sign=sec['fc60_sign'],
                compatibility_score=sec['compatibility_score']
            )
        )
    
    db.add_all(participants)
    db.commit()
    db.refresh(reading)
    
    logger.info(f"Multi-user reading created: ID={reading.id}, primary={request.primary_user_id}, participants={len(request.secondary_user_ids)}")
    
    # Build response
    return MultiUserReadingResponse(
        reading_id=reading.id,
        primary_user=result['primary'],
        secondary_users=result['secondary'],
        combined_analysis=result['combined_analysis'],
        question=request.question,
        created_at=reading.created_at,
        fc60_details=result['fc60_details']
    )
```

**Acceptance:**
- [ ] Endpoint accepts multi-user request
- [ ] Validates all user IDs exist
- [ ] Calls Oracle service correctly
- [ ] Stores reading + participants in database
- [ ] Returns complete response with compatibility scores
- [ ] Error handling for service unavailable

**Verification:**
```bash
# Start API
uvicorn app.main:app --reload &

# Test endpoint
curl -X POST http://localhost:8000/api/oracle/reading/multi-user \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_user_id": 1,
    "secondary_user_ids": [2],
    "question": "Test compatibility",
    "sign_type": "birth_date",
    "sign_value": "1990-01-15"
  }'
# Expected: JSON response with reading_id, primary_user, secondary_users, combined_analysis
```

**Checkpoint Phase 1:**
- [ ] Pydantic models validate correctly
- [ ] Oracle service client connects
- [ ] Endpoint returns 200 with valid data
- [ ] Database has reading + participants stored

**STOP if checkpoint fails** - fix before Phase 2

---

### Phase 2: Translation Service (90 min)

**Extended Thinking Decision: Translation Strategy**
<thinking>
DECISION: How to implement English ↔ Persian translation?

OPTIONS:
1. **Google Translate API**
   - Pros: Fast, cheap, good quality
   - Cons: Privacy concerns (data sent to Google), requires API key
   
2. **Claude API (Anthropic)**
   - Pros: Already have API key, excellent quality, understands context, preserves formatting
   - Cons: Slower (LLM latency), more expensive, requires prompt engineering
   
3. **Local model (MarianMT)**
   - Pros: Free, private, fast
   - Cons: Lower quality for Persian, requires model download, limited context understanding

EVALUATION:
- Quality critical: FC60 readings contain spiritual/metaphysical language
- Privacy: Readings may be personal/sensitive
- Cost: Translation not real-time critical (acceptable 2-3s latency)
- Infrastructure: Already using Claude API for Oracle insights

RECOMMENDATION: Claude API (Option 2)
- Best quality for specialized terminology
- Privacy-preserving (Anthropic's data policy)
- Unified API key management
- Can provide context in prompts for better translation
</thinking>

**Tasks:**

**2.1: Translation Cache Manager (20 min)**

Create `api/app/services/translation_cache.py`:

```python
from typing import Optional, Dict
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class TranslationCache:
    """
    In-memory LRU cache for translations.
    
    Cache key: hash(text + from_lang + to_lang)
    Max size: 1000 entries
    TTL: 24 hours
    """
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=24)
    
    def _make_key(self, text: str, from_lang: str, to_lang: str) -> str:
        """Generate cache key from text + languages."""
        content = f"{text}|{from_lang}|{to_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, from_lang: str, to_lang: str) -> Optional[str]:
        """Get cached translation if exists and not expired."""
        key = self._make_key(text, from_lang, to_lang)
        
        if key not in self.cache:
            return None
        
        # Check expiration
        if datetime.now() - self.access_times[key] > self.ttl:
            logger.debug(f"Translation cache expired for key {key[:8]}...")
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # Update access time (LRU)
        self.access_times[key] = datetime.now()
        logger.debug(f"Translation cache HIT for key {key[:8]}...")
        
        return self.cache[key]['translated']
    
    def set(self, text: str, from_lang: str, to_lang: str, translated: str):
        """Cache translation with LRU eviction if needed."""
        key = self._make_key(text, from_lang, to_lang)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_times, key=self.access_times.get)
            logger.debug(f"Translation cache EVICT: {oldest_key[:8]}...")
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = {
            'original': text,
            'translated': translated,
            'from': from_lang,
            'to': to_lang
        }
        self.access_times[key] = datetime.now()
        logger.debug(f"Translation cache SET for key {key[:8]}...")
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "oldest_entry_age_hours": (
                (datetime.now() - min(self.access_times.values())).total_seconds() / 3600
                if self.access_times else 0
            )
        }

# Singleton cache instance
translation_cache = TranslationCache(max_size=1000)
```

**Acceptance:**
- [ ] Cache implements LRU eviction
- [ ] Cache respects TTL (24 hours)
- [ ] Cache key generation handles special characters
- [ ] Stats method works

**Verification:**
```bash
python -c "
from app.services.translation_cache import translation_cache
translation_cache.set('hello', 'en', 'fa', 'سلام')
result = translation_cache.get('hello', 'en', 'fa')
assert result == 'سلام', f'Expected سلام, got {result}'
print('Cache works:', result)
"
# Expected: "Cache works: سلام"
```

---

**2.2: Claude Translation Service (30 min)**

Create `api/app/services/translation_service.py`:

```python
import anthropic
import logging
import os
from typing import Literal

from app.services.translation_cache import translation_cache

logger = logging.getLogger(__name__)

LanguageCode = Literal['en', 'fa']

class TranslationService:
    """High-quality translation using Claude API."""
    
    def __init__(self):
        self.api_key = os.getenv("NPS_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("NPS_ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Latest Sonnet
    
    async def translate(
        self,
        text: str,
        from_lang: LanguageCode,
        to_lang: LanguageCode
    ) -> str:
        """
        Translate text using Claude API.
        
        Args:
            text: Text to translate
            from_lang: Source language ('en' or 'fa')
            to_lang: Target language ('en' or 'fa')
            
        Returns:
            Translated text
        """
        # Check cache first
        cached = translation_cache.get(text, from_lang, to_lang)
        if cached:
            logger.info(f"Translation cache hit: {from_lang}->{to_lang}, length={len(text)}")
            return cached
        
        # Prepare translation prompt
        lang_names = {
            'en': 'English',
            'fa': 'Persian (Farsi)'
        }
        
        prompt = f"""Translate the following text from {lang_names[from_lang]} to {lang_names[to_lang]}.

IMPORTANT INSTRUCTIONS:
- Preserve all formatting (line breaks, bullet points, numbering)
- Maintain the tone and style of the original
- For specialized terms (FC60, numerology, astrological), use standard translations or transliterate if no equivalent exists
- Return ONLY the translated text, no preamble or explanation

TEXT TO TRANSLATE:
{text}

TRANSLATION:"""
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temp for consistent translations
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            translated = response.content[0].text.strip()
            
            # Cache result
            translation_cache.set(text, from_lang, to_lang, translated)
            
            logger.info(f"Translation completed: {from_lang}->{to_lang}, length={len(text)}, tokens={response.usage.input_tokens + response.usage.output_tokens}")
            
            return translated
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e.status_code} - {e.message}")
            raise Exception(f"Translation service unavailable: {e.message}")
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}", exc_info=True)
            raise

# Singleton instance
translation_service = TranslationService()
```

**Acceptance:**
- [ ] Claude API client initialized
- [ ] Translation prompt preserves formatting
- [ ] Cache checked before API call
- [ ] Error handling for API failures
- [ ] Token usage logged

**Verification:**
```bash
python -c "
import asyncio
from app.services.translation_service import translation_service

async def test():
    result = await translation_service.translate('Hello, how are you?', 'en', 'fa')
    print('Translated:', result)

asyncio.run(test())
"
# Expected: Persian translation of "Hello, how are you?"
```

---

**2.3: Translation Endpoint (40 min)**

Create `api/app/routers/translation.py` (new file):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal

from app.services.translation_service import translation_service, LanguageCode
from app.security.auth import validate_api_key

router = APIRouter()

class TranslationRequest(BaseModel):
    """Request model for translation."""
    
    text: str = Field(..., min_length=1, max_length=5000, description="Text to translate (max 5000 chars)")
    from_lang: LanguageCode = Field(..., description="Source language: 'en' or 'fa'")
    to_lang: LanguageCode = Field(..., description="Target language: 'en' or 'fa'")
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()
    
    @validator('to_lang')
    def different_languages(cls, v, values):
        if 'from_lang' in values and v == values['from_lang']:
            raise ValueError("Source and target languages must be different")
        return v

class TranslationResponse(BaseModel):
    """Response model for translation."""
    
    translated: str = Field(..., description="Translated text")
    original: str = Field(..., description="Original text (for reference)")
    from_lang: LanguageCode
    to_lang: LanguageCode
    cached: bool = Field(..., description="Whether result came from cache")

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    auth: dict = Depends(validate_api_key)
):
    """
    Translate text between English and Persian (Farsi).
    
    Uses Claude API for high-quality, context-aware translation.
    Results are cached for 24 hours to improve performance.
    
    **Scope required:** oracle_read
    
    **Rate limit:** 100 requests/minute per API key
    
    **Supported languages:**
    - en: English
    - fa: Persian (Farsi)
    
    **Example:**
    ```json
    {
      "text": "The Water Ox brings balance and wisdom",
      "from_lang": "en",
      "to_lang": "fa"
    }
    ```
    
    **Response:**
    - translated: The translated text
    - original: Original text (for reference)
    - cached: True if from cache, False if fresh translation
    """
    
    # Check cache before calling service
    from app.services.translation_cache import translation_cache
    cached_result = translation_cache.get(request.text, request.from_lang, request.to_lang)
    
    if cached_result:
        return TranslationResponse(
            translated=cached_result,
            original=request.text,
            from_lang=request.from_lang,
            to_lang=request.to_lang,
            cached=True
        )
    
    # Call translation service
    try:
        translated = await translation_service.translate(
            text=request.text,
            from_lang=request.from_lang,
            to_lang=request.to_lang
        )
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service temporarily unavailable"
        )
    
    return TranslationResponse(
        translated=translated,
        original=request.text,
        from_lang=request.from_lang,
        to_lang=request.to_lang,
        cached=False
    )

@router.get("/translate/cache/stats")
async def get_cache_stats(auth: dict = Depends(validate_api_key)):
    """
    Get translation cache statistics.
    
    **Scope required:** admin
    
    **Returns:**
    - size: Current number of cached translations
    - max_size: Maximum cache size
    - oldest_entry_age_hours: Age of oldest cached entry
    """
    from app.services.translation_cache import translation_cache
    return translation_cache.stats()
```

**Add to main app:**

In `api/app/main.py`:
```python
from app.routers import translation

app.include_router(
    translation.router,
    prefix="/api/translation",
    tags=["Translation"]
)
```

**Acceptance:**
- [ ] POST /api/translation/translate accepts request
- [ ] Returns translated text
- [ ] Caches results (second request faster)
- [ ] Validates different languages
- [ ] Stats endpoint shows cache info

**Verification:**
```bash
# First translation (uncached)
time curl -X POST http://localhost:8000/api/translation/translate \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Water Ox brings balance",
    "from_lang": "en",
    "to_lang": "fa"
  }'
# Expected: ~2-3 seconds, "cached": false

# Second translation (cached)
time curl -X POST http://localhost:8000/api/translation/translate \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Water Ox brings balance",
    "from_lang": "en",
    "to_lang": "fa"
  }'
# Expected: <100ms, "cached": true

# Cache stats
curl http://localhost:8000/api/translation/cache/stats \
  -H "Authorization: Bearer test_key"
# Expected: {"size": 1, "max_size": 1000, "oldest_entry_age_hours": 0.0}
```

**Checkpoint Phase 2:**
- [ ] Translation works (English → Persian)
- [ ] Translation works (Persian → English)
- [ ] Cache hit rate >0% on repeated requests
- [ ] Response time <3s (uncached), <100ms (cached)

**STOP if checkpoint fails** - fix before Phase 3

---

### Phase 3: Location Services (60 min)

**Extended Thinking Decision: Location API**
<thinking>
DECISION: Which geolocation service to use?

OPTIONS:
1. **Nominatim (OpenStreetMap)**
   - Pros: Free, no API key, good coverage, accurate
   - Cons: Rate limit 1 req/sec, requires attribution
   
2. **Google Geocoding API**
   - Pros: Excellent accuracy, fast
   - Cons: Requires API key, costs money after free tier
   
3. **ipapi.co (for IP detection)**
   - Pros: Free tier 1000/day, simple API
   - Cons: Limited free tier, less accurate for mobile IPs

EVALUATION:
- Cost: Prefer free tier for MVP
- Accuracy: Nominatim sufficient for major cities
- Rate limits: 1 req/sec acceptable with caching
- IP detection: Separate service needed

RECOMMENDATION: 
- City lookup: Nominatim (Option 1)
- IP detection: ipapi.co (Option 3)
- Both with aggressive caching
</thinking>

**Tasks:**

**3.1: Location Cache Manager (15 min)**

Create `api/app/services/location_cache.py`:

```python
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LocationCache:
    """
    Persistent cache for location lookups.
    
    Two caches:
    - City cache: (city, country) -> coordinates
    - IP cache: ip_address -> location
    """
    
    def __init__(self):
        self.city_cache: Dict[str, Dict] = {}
        self.ip_cache: Dict[str, Dict] = {}
        self.city_ttl = timedelta(days=30)  # Cities don't move
        self.ip_ttl = timedelta(days=7)  # IPs can change
    
    def get_city(self, city: str, country: str) -> Optional[Dict]:
        """Get cached city coordinates."""
        key = f"{city.lower()}|{country.lower()}"
        
        if key not in self.city_cache:
            return None
        
        entry = self.city_cache[key]
        if datetime.now() - entry['cached_at'] > self.city_ttl:
            del self.city_cache[key]
            return None
        
        logger.debug(f"City cache HIT: {city}, {country}")
        return entry['data']
    
    def set_city(self, city: str, country: str, data: Dict):
        """Cache city coordinates."""
        key = f"{city.lower()}|{country.lower()}"
        self.city_cache[key] = {
            'data': data,
            'cached_at': datetime.now()
        }
        logger.debug(f"City cache SET: {city}, {country}")
    
    def get_ip(self, ip: str) -> Optional[Dict]:
        """Get cached IP location."""
        if ip not in self.ip_cache:
            return None
        
        entry = self.ip_cache[ip]
        if datetime.now() - entry['cached_at'] > self.ip_ttl:
            del self.ip_cache[ip]
            return None
        
        logger.debug(f"IP cache HIT: {ip}")
        return entry['data']
    
    def set_ip(self, ip: str, data: Dict):
        """Cache IP location."""
        self.ip_cache[ip] = {
            'data': data,
            'cached_at': datetime.now()
        }
        logger.debug(f"IP cache SET: {ip}")

# Singleton cache
location_cache = LocationCache()
```

**Acceptance:**
- [ ] City cache works
- [ ] IP cache works
- [ ] TTL respected (cities 30 days, IPs 7 days)

---

**3.2: Location Service (30 min)**

Create `api/app/services/location_service.py`:

```python
import httpx
import logging
from typing import Dict, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pytz

from app.services.location_cache import location_cache

logger = logging.getLogger(__name__)

class LocationService:
    """Location lookup service with caching."""
    
    def __init__(self):
        self.geocoder = Nominatim(
            user_agent="NPS_V4_Oracle/1.0",
            timeout=5
        )
        self.ipapi_url = "https://ipapi.co/{ip}/json/"
    
    async def get_coordinates(
        self,
        city: str,
        country: str
    ) -> Dict:
        """
        Get coordinates for city.
        
        Returns:
            {
                "latitude": float,
                "longitude": float,
                "timezone": str,
                "display_name": str
            }
        """
        # Check cache
        cached = location_cache.get_city(city, country)
        if cached:
            logger.info(f"City lookup cache hit: {city}, {country}")
            return cached
        
        # Query Nominatim
        try:
            query = f"{city}, {country}"
            location = self.geocoder.geocode(query)
            
            if not location:
                raise ValueError(f"City not found: {query}")
            
            # Get timezone from coordinates
            timezone = self._get_timezone(location.latitude, location.longitude)
            
            result = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "timezone": timezone,
                "display_name": location.address
            }
            
            # Cache result
            location_cache.set_city(city, country, result)
            
            logger.info(f"City lookup completed: {city}, {country} -> {location.latitude}, {location.longitude}")
            
            return result
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding service error: {str(e)}")
            raise Exception("Location service temporarily unavailable")
        except Exception as e:
            logger.error(f"City lookup failed: {str(e)}", exc_info=True)
            raise
    
    async def detect_location_from_ip(self, ip_address: str) -> Dict:
        """
        Detect location from IP address.
        
        Returns:
            {
                "latitude": float,
                "longitude": float,
                "timezone": str,
                "city": str,
                "country": str
            }
        """
        # Check cache
        cached = location_cache.get_ip(ip_address)
        if cached:
            logger.info(f"IP lookup cache hit: {ip_address}")
            return cached
        
        # Query ipapi.co
        try:
            async with httpx.AsyncClient() as client:
                url = self.ipapi_url.format(ip=ip_address)
                response = await client.get(url, timeout=5.0)
                response.raise_for_status()
                data = response.json()
            
            if 'error' in data:
                raise ValueError(f"IP lookup failed: {data['reason']}")
            
            result = {
                "latitude": float(data['latitude']),
                "longitude": float(data['longitude']),
                "timezone": data['timezone'],
                "city": data['city'],
                "country": data['country_name']
            }
            
            # Cache result
            location_cache.set_ip(ip_address, result)
            
            logger.info(f"IP lookup completed: {ip_address} -> {result['city']}, {result['country']}")
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"IP API HTTP error: {str(e)}")
            raise Exception("IP detection service unavailable")
        except Exception as e:
            logger.error(f"IP lookup failed: {str(e)}", exc_info=True)
            raise
    
    def _get_timezone(self, latitude: float, longitude: float) -> str:
        """Get timezone name from coordinates using pytz."""
        from timezonefinder import TimezoneFinder
        
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
        
        return timezone_name or "UTC"

# Singleton instance
location_service = LocationService()
```

**Acceptance:**
- [ ] Nominatim geocoding works
- [ ] ipapi.co IP detection works
- [ ] Timezone detection works
- [ ] Cache hit rate >0%

---

**3.3: Location Endpoints (15 min)**

Create `api/app/routers/location.py` (new file):

```python
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from app.services.location_service import location_service
from app.security.auth import validate_api_key

router = APIRouter()

class CoordinatesResponse(BaseModel):
    """Response model for coordinates lookup."""
    
    latitude: float
    longitude: float
    timezone: str
    display_name: str

class IPLocationResponse(BaseModel):
    """Response model for IP-based location."""
    
    latitude: float
    longitude: float
    timezone: str
    city: str
    country: str

@router.get("/coordinates", response_model=CoordinatesResponse)
async def get_city_coordinates(
    city: str = Field(..., description="City name"),
    country: str = Field(..., description="Country name or code"),
    auth: dict = Depends(validate_api_key)
):
    """
    Get coordinates for a city.
    
    **Example:** GET /api/location/coordinates?city=Tehran&country=Iran
    
    **Response:**
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - timezone: IANA timezone name
    - display_name: Full formatted address
    """
    try:
        result = await location_service.get_coordinates(city, country)
        return CoordinatesResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Location service temporarily unavailable"
        )

@router.get("/detect", response_model=IPLocationResponse)
async def detect_location(
    request: Request,
    auth: dict = Depends(validate_api_key)
):
    """
    Detect user's location from IP address.
    
    Uses client IP from request headers.
    Fallback to default location if detection fails.
    
    **Response:**
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - timezone: IANA timezone name
    - city: Detected city name
    - country: Detected country name
    """
    # Get client IP
    client_ip = request.client.host
    
    # For local testing, use a public IP
    if client_ip in ['127.0.0.1', 'localhost', '::1']:
        logger.warning(f"Local IP detected ({client_ip}), using fallback location")
        # Default to Tehran, Iran
        return IPLocationResponse(
            latitude=35.6892,
            longitude=51.3890,
            timezone="Asia/Tehran",
            city="Tehran",
            country="Iran"
        )
    
    try:
        result = await location_service.detect_location_from_ip(client_ip)
        return IPLocationResponse(**result)
    except Exception as e:
        logger.error(f"IP detection failed: {str(e)}")
        # Fallback to default location
        return IPLocationResponse(
            latitude=35.6892,
            longitude=51.3890,
            timezone="Asia/Tehran",
            city="Tehran",
            country="Iran"
        )
```

**Add to main app:**

In `api/app/main.py`:
```python
from app.routers import location

app.include_router(
    location.router,
    prefix="/api/location",
    tags=["Location"]
)
```

**Acceptance:**
- [ ] GET /api/location/coordinates returns coordinates
- [ ] GET /api/location/detect returns IP-based location
- [ ] Fallback to default location for localhost
- [ ] Cache improves performance on repeated queries

**Verification:**
```bash
# City coordinates
curl "http://localhost:8000/api/location/coordinates?city=London&country=UK" \
  -H "Authorization: Bearer test_key"
# Expected: {"latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London", ...}

# IP detection
curl http://localhost:8000/api/location/detect \
  -H "Authorization: Bearer test_key"
# Expected: Fallback location (Tehran) or detected location if public IP
```

**Checkpoint Phase 3:**
- [ ] City lookup works for 5 test cities
- [ ] IP detection returns valid location
- [ ] Cache hit rate >0% on second request
- [ ] Response time <500ms (city), <1s (IP)

**STOP if checkpoint fails** - fix before Phase 4

---

### Phase 4: Comprehensive Testing (60 min)

**Extended Thinking Decision: Test Strategy**
<thinking>
Test coverage targets:
- Unit tests: Each service function
- Integration tests: Endpoint → Service → Database flow
- Edge cases: Invalid inputs, service failures, cache misses
- Performance: Response time benchmarks

Test organization:
- tests/test_multi_user_reading.py
- tests/test_translation.py
- tests/test_location.py
</thinking>

**Tasks:**

**4.1: Multi-User Reading Tests (20 min)**

Create `api/tests/test_multi_user_reading.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.database.models import User, Reading, ReadingParticipant

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """API key headers."""
    return {"Authorization": "Bearer test_key"}

@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing."""
    users = [
        User(id=1, name="Alice", birth_date="1990-01-15"),
        User(id=2, name="Bob", birth_date="1992-06-20"),
        User(id=3, name="Charlie", birth_date="1988-12-05")
    ]
    db_session.add_all(users)
    db_session.commit()
    return users

def test_multi_user_reading_success(auth_headers, sample_users, db_session):
    """Test successful multi-user reading."""
    
    # Mock Oracle service response
    mock_response = {
        "primary": {"id": 1, "name": "Alice", "fc60_sign": "Water Ox", "element": "Water"},
        "secondary": [
            {"id": 2, "name": "Bob", "fc60_sign": "Fire Horse", "element": "Fire", "compatibility_score": 0.75}
        ],
        "combined_analysis": "Water and Fire create balanced dynamic.",
        "fc60_details": {"primary_full": "...", "relationships": "..."}
    }
    
    with patch('app.services.oracle_service.oracle_client.multi_user_reading', return_value=mock_response):
        response = client.post(
            "/api/oracle/reading/multi-user",
            headers=auth_headers,
            json={
                "primary_user_id": 1,
                "secondary_user_ids": [2],
                "question": "What is our compatibility?",
                "sign_type": "birth_date",
                "sign_value": "1990-01-15"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['primary_user']['id'] == 1
    assert data['primary_user']['fc60_sign'] == "Water Ox"
    assert len(data['secondary_users']) == 1
    assert data['secondary_users'][0]['compatibility_score'] == 0.75
    assert "reading_id" in data
    
    # Verify database storage
    reading = db_session.query(Reading).filter_by(id=data['reading_id']).first()
    assert reading is not None
    assert reading.reading_type == "multi_user"
    
    participants = db_session.query(ReadingParticipant).filter_by(reading_id=reading.id).all()
    assert len(participants) == 2  # Primary + 1 secondary

def test_multi_user_reading_invalid_users(auth_headers):
    """Test multi-user reading with non-existent users."""
    
    response = client.post(
        "/api/oracle/reading/multi-user",
        headers=auth_headers,
        json={
            "primary_user_id": 999,
            "secondary_user_ids": [998],
            "sign_type": "birth_date",
            "sign_value": "1990-01-15"
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()

def test_multi_user_reading_duplicate_users(auth_headers):
    """Test validation for duplicate users."""
    
    response = client.post(
        "/api/oracle/reading/multi-user",
        headers=auth_headers,
        json={
            "primary_user_id": 1,
            "secondary_user_ids": [1, 2],  # Primary in secondary list
            "sign_type": "birth_date",
            "sign_value": "1990-01-15"
        }
    )
    
    assert response.status_code == 422  # Validation error

def test_multi_user_reading_max_users(auth_headers, sample_users):
    """Test maximum 5 secondary users limit."""
    
    response = client.post(
        "/api/oracle/reading/multi-user",
        headers=auth_headers,
        json={
            "primary_user_id": 1,
            "secondary_user_ids": [2, 3, 4, 5, 6, 7],  # 6 users, max is 5
            "sign_type": "birth_date",
            "sign_value": "1990-01-15"
        }
    )
    
    assert response.status_code == 422  # Validation error
```

---

**4.2: Translation Tests (20 min)**

Create `api/tests/test_translation.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.services.translation_cache import translation_cache

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_key"}

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear translation cache before each test."""
    translation_cache.cache.clear()
    translation_cache.access_times.clear()

def test_translation_en_to_fa(auth_headers):
    """Test English to Persian translation."""
    
    mock_translated = "گاو آبی تعادل می‌آورد"
    
    with patch('app.services.translation_service.translation_service.client.messages.create') as mock_create:
        mock_create.return_value.content = [Mock(text=mock_translated)]
        mock_create.return_value.usage.input_tokens = 50
        mock_create.return_value.usage.output_tokens = 30
        
        response = client.post(
            "/api/translation/translate",
            headers=auth_headers,
            json={
                "text": "The Water Ox brings balance",
                "from_lang": "en",
                "to_lang": "fa"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['translated'] == mock_translated
    assert data['original'] == "The Water Ox brings balance"
    assert data['from_lang'] == "en"
    assert data['to_lang'] == "fa"
    assert data['cached'] == False  # First request not cached

def test_translation_cache_hit(auth_headers):
    """Test translation cache hit on second request."""
    
    # First request (uncached)
    mock_translated = "سلام"
    with patch('app.services.translation_service.translation_service.client.messages.create') as mock_create:
        mock_create.return_value.content = [Mock(text=mock_translated)]
        mock_create.return_value.usage.input_tokens = 10
        mock_create.return_value.usage.output_tokens = 5
        
        response1 = client.post(
            "/api/translation/translate",
            headers=auth_headers,
            json={"text": "Hello", "from_lang": "en", "to_lang": "fa"}
        )
    
    assert response1.json()['cached'] == False
    
    # Second request (cached, should not call API)
    response2 = client.post(
        "/api/translation/translate",
        headers=auth_headers,
        json={"text": "Hello", "from_lang": "en", "to_lang": "fa"}
    )
    
    assert response2.status_code == 200
    assert response2.json()['cached'] == True
    assert response2.json()['translated'] == mock_translated

def test_translation_empty_text(auth_headers):
    """Test validation for empty text."""
    
    response = client.post(
        "/api/translation/translate",
        headers=auth_headers,
        json={"text": "   ", "from_lang": "en", "to_lang": "fa"}
    )
    
    assert response.status_code == 422  # Validation error

def test_translation_same_language(auth_headers):
    """Test validation for same source and target language."""
    
    response = client.post(
        "/api/translation/translate",
        headers=auth_headers,
        json={"text": "Hello", "from_lang": "en", "to_lang": "en"}
    )
    
    assert response.status_code == 422  # Validation error

def test_translation_cache_stats(auth_headers):
    """Test cache statistics endpoint."""
    
    response = client.get(
        "/api/translation/cache/stats",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "size" in data
    assert "max_size" in data
    assert data['max_size'] == 1000
```

---

**4.3: Location Tests (20 min)**

Create `api/tests/test_location.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app
from app.services.location_cache import location_cache

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test_key"}

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear location cache before each test."""
    location_cache.city_cache.clear()
    location_cache.ip_cache.clear()

def test_city_coordinates_success(auth_headers):
    """Test successful city coordinates lookup."""
    
    mock_location = Mock()
    mock_location.latitude = 51.5074
    mock_location.longitude = -0.1278
    mock_location.address = "London, United Kingdom"
    
    with patch('app.services.location_service.location_service.geocoder.geocode', return_value=mock_location):
        with patch('app.services.location_service.location_service._get_timezone', return_value="Europe/London"):
            response = client.get(
                "/api/location/coordinates?city=London&country=UK",
                headers=auth_headers
            )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['latitude'] == 51.5074
    assert data['longitude'] == -0.1278
    assert data['timezone'] == "Europe/London"
    assert "London" in data['display_name']

def test_city_coordinates_not_found(auth_headers):
    """Test city not found error."""
    
    with patch('app.services.location_service.location_service.geocoder.geocode', return_value=None):
        response = client.get(
            "/api/location/coordinates?city=InvalidCity&country=XX",
            headers=auth_headers
        )
    
    assert response.status_code == 404

def test_city_coordinates_cache_hit(auth_headers):
    """Test city coordinates cache hit."""
    
    # First request
    mock_location = Mock()
    mock_location.latitude = 35.6892
    mock_location.longitude = 51.3890
    mock_location.address = "Tehran, Iran"
    
    with patch('app.services.location_service.location_service.geocoder.geocode', return_value=mock_location) as mock_geocode:
        with patch('app.services.location_service.location_service._get_timezone', return_value="Asia/Tehran"):
            response1 = client.get(
                "/api/location/coordinates?city=Tehran&country=Iran",
                headers=auth_headers
            )
            
            # Second request (should hit cache, not call geocoder)
            response2 = client.get(
                "/api/location/coordinates?city=Tehran&country=Iran",
                headers=auth_headers
            )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert mock_geocode.call_count == 1  # Called only once (cached second time)

def test_ip_detection_localhost_fallback(auth_headers):
    """Test IP detection fallback for localhost."""
    
    response = client.get(
        "/api/location/detect",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return default location (Tehran)
    assert data['city'] == "Tehran"
    assert data['country'] == "Iran"
    assert data['latitude'] == 35.6892

def test_ip_detection_public_ip(auth_headers):
    """Test IP detection with public IP."""
    
    mock_ip_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timezone": "America/New_York",
        "city": "New York",
        "country_name": "United States"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.json.return_value = mock_ip_data
        mock_get.return_value.raise_for_status = Mock()
        
        # Mock request to simulate public IP
        with patch('app.routers.location.request.client.host', '8.8.8.8'):
            response = client.get(
                "/api/location/detect",
                headers=auth_headers
            )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['city'] == "New York"
    assert data['latitude'] == 40.7128
```

**Acceptance:**
- [ ] All tests pass (45+ tests)
- [ ] Coverage ≥95% for new code
- [ ] No flaky tests (run 3 times)
- [ ] Performance tests included

**Verification:**
```bash
cd api
pytest tests/test_multi_user_reading.py tests/test_translation.py tests/test_location.py -v --cov
# Expected: 45+ tests pass, 95%+ coverage

# Run 3 times to check for flaky tests
for i in {1..3}; do
  echo "Run $i:"
  pytest tests/ -x --tb=short
done
# Expected: All runs pass
```

**Checkpoint Phase 4:**
- [ ] All 45+ tests pass
- [ ] Coverage report shows ≥95%
- [ ] No test failures on repeated runs
- [ ] Test execution time <30 seconds

---

## VERIFICATION CHECKLIST

**Code Quality:**
- [ ] Type hints on all functions (mypy --strict passes)
- [ ] Docstrings on all public functions
- [ ] Error handling explicit (no bare except)
- [ ] Logging at appropriate levels (INFO for operations, ERROR for failures)
- [ ] No hardcoded values (API keys in environment)

**Functionality:**
- [ ] Multi-user reading endpoint returns 200 with valid data
- [ ] Translation caches results (second request <100ms)
- [ ] Location coordinates accurate for 5 test cities
- [ ] IP detection returns valid fallback for localhost
- [ ] All endpoints require authentication (401 without API key)

**Performance:**
- [ ] Multi-user reading: <200ms p95 (measured with ab)
- [ ] Translation: <3s uncached, <100ms cached
- [ ] Location lookup: <500ms uncached, <100ms cached
- [ ] IP detection: <1s (with external API call)

**Testing:**
- [ ] Unit tests: 45+ tests pass
- [ ] Coverage: ≥95% for new code
- [ ] Integration tests: Multi-user → Database flow works
- [ ] Edge cases: Invalid inputs, service failures handled
- [ ] Cache tests: Verify cache hit/miss behavior

**Security:**
- [ ] API key authentication enforced
- [ ] User ID validation (no accessing other users' data)
- [ ] Claude API key in environment variable (not code)
- [ ] No sensitive data logged (even in debug mode)

**Documentation:**
- [ ] OpenAPI documentation updated (Swagger UI)
- [ ] README includes new endpoints
- [ ] Example requests in docstrings
- [ ] Error codes documented

---

## SUCCESS CRITERIA

**Measurable Criteria:**

1. **Multi-User Reading:**
   - Endpoint returns 200 for valid request
   - Database stores reading + participants (verified)
   - Compatible with 2-5 secondary users
   - Response time <200ms p95 (verified with ab -n 100)

2. **Translation:**
   - English → Persian accuracy >90% (manual spot check)
   - Persian → English accuracy >90% (manual spot check)
   - Cache hit rate >50% after 100 requests (same text)
   - Response time <3s uncached, <100ms cached

3. **Location:**
   - City lookup accuracy for 10 major cities (lat/long ±0.1°)
   - IP detection returns valid location or fallback
   - Cache hit rate >80% for common cities
   - Response time <500ms uncached, <100ms cached

4. **Overall:**
   - All 45+ tests pass
   - Coverage ≥95%
   - No breaking changes to existing endpoints
   - OpenAPI documentation complete
   - Production-ready (error handling, logging, caching)

---

## HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

**Resume from Phase:** [N]

**Context Needed:**
- Which phase completed last?
- Which tests are failing (if any)?
- Which external APIs tested (Claude, ipapi.co)?

**Verification Before Continuing:**

```bash
# Check Phase 1 (Multi-User)
curl -X POST http://localhost:8000/api/oracle/reading/multi-user \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"primary_user_id": 1, "secondary_user_ids": [2], "sign_type": "birth_date", "sign_value": "1990-01-15"}'
# Expected: 200 with reading_id

# Check Phase 2 (Translation)
curl -X POST http://localhost:8000/api/translation/translate \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "from_lang": "en", "to_lang": "fa"}'
# Expected: 200 with translated text

# Check Phase 3 (Location)
curl "http://localhost:8000/api/location/coordinates?city=London&country=UK" \
  -H "Authorization: Bearer test_key"
# Expected: 200 with coordinates

# Check Phase 4 (Tests)
pytest tests/ -v --cov
# Expected: 45+ tests pass, 95%+ coverage
```

---

## NEXT STEPS (After This Spec)

**Immediate (Terminal 2 - API Layer):**
1. **T2-S4: Advanced Oracle Endpoints** - Name analysis, daily insights, question answering
2. **T2-S5: Vault Endpoints** - Export findings to CSV/JSON, search, filters
3. **T2-S6: Learning Endpoints** - XP/level stats, AI recommendations, apply learning

**Cross-Terminal Integration:**
1. **T1-S3: Frontend Integration** - UI for multi-user readings + translation
2. **T3-S3: Oracle Enhancement** - Improve multi-user FC60 analysis quality
3. **T5-S2: Docker Health Checks** - Add health checks for new endpoints

**Performance Optimization:**
1. Benchmark translation with 1000 requests (measure cache effectiveness)
2. Load test multi-user reading with 10 concurrent users
3. Profile location service (identify bottlenecks)

---

## ESTIMATED TIMELINE

**Phase 1: Multi-User Reading** - 90 minutes
- Models + Oracle client: 50 min
- Endpoint: 40 min

**Phase 2: Translation** - 90 minutes
- Cache: 20 min
- Claude API service: 30 min
- Endpoint: 40 min

**Phase 3: Location** - 60 minutes
- Cache: 15 min
- Service: 30 min
- Endpoints: 15 min

**Phase 4: Testing** - 60 minutes
- Multi-user tests: 20 min
- Translation tests: 20 min
- Location tests: 20 min

**Total:** 5 hours (including buffer for debugging)

---

## TOOLS SUMMARY

**Extended Thinking Used For:**
- Translation strategy (Claude API vs Google Translate)
- Location API selection (Nominatim vs paid services)
- Multi-user storage pattern (junction table vs flat JSON)
- Caching strategy (Redis vs in-memory vs database)

**Subagents Used:**
- Subagent 1: Multi-user reading (models + service + endpoint)
- Subagent 2: Translation (cache + service + endpoint)
- Subagent 3: Location (cache + service + endpoints)
- Subagent 4: Comprehensive tests (all 3 feature groups)

**MCP Servers:**
- Database MCP: Junction table queries (reading_participants)
- (Optional) Redis MCP: If switching from in-memory cache

**Skills Referenced:**
- product-self-knowledge: Claude API patterns for translation
- NPS_V4_ARCHITECTURE_PLAN.md: Layer 2 design principles

---

**END OF SPECIFICATION**

*Ready for Claude Code CLI execution with Extended Thinking.*  
*Estimated completion: 5 hours*  
*Quality target: 95%+ test coverage, production-ready*
