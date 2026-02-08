# SPEC: Backend AI Integration - T3-S3
**Estimated Duration:** 4-5 hours  
**Layer:** Layer 3 (Backend - Oracle Service)  
**Terminal:** Terminal 3  
**Phase:** Phase 2 (Services)  
**Session:** T3-S3 (AI Integration)

---

## TL;DR
- Integrate Claude API for enhanced AI interpretations and translations
- Four interpretation formats: Simple, Person-to-Person, Action Steps, Universe Message
- Multi-user insights with group dynamics and compatibility analysis
- English ↔ Persian translation with cultural adaptation
- Context-aware prompts using FC60 data
- Deliverable: 3 new Python modules with 95%+ test coverage
- Verification: API calls succeed with culturally appropriate responses

---

## OBJECTIVE

Implement Claude API integration in the Oracle service to provide:
1. **Enhanced interpretations** in 4 formats tailored to user preferences
2. **Multi-user insights** for groups/partnerships with compatibility analysis
3. **Translation service** (English ↔ Persian) preserving numerology context

**Success Metric:** Claude API responds in <3s with culturally appropriate, actionable wisdom

---

## CONTEXT

**Current State:**
- Terminal 3 Session 1 completed: FC60 Core engine (encoding, decoding, meanings)
- Terminal 3 Session 2 completed: Multi-user FC60 (compatibility, group dynamics)
- Oracle service returns FC60 signatures but lacks human-friendly explanations
- No translation capability (English only)

**What's Changing:**
- Adding AI interpretation module using Claude API
- Creating prompt templates for each interpretation format
- Implementing translation service with context preservation
- Extending multi-user analysis with partnership guidance

**Why:**
From NPS V4 Architecture Plan (Layer 3B - Oracle Service):
> "Oracle service analyzes patterns in successful wallet findings to suggest lucky ranges for Scanner"
> "Use AI to find correlations and generate human-readable insights"

Current FC60 outputs like "Water Ox in Receptive Gate" are mystical but not actionable. Users need:
- Simple explanations (for beginners)
- Personal advice (for decision-making)
- Concrete actions (for immediate use)
- Inspirational messages (for reflection)

---

## PREREQUISITES

**Environment:**
- [ ] Python 3.11+ installed (verify: `python --version`)
- [ ] Virtual environment activated (verify: `which python` shows venv)
- [ ] Terminal 3 Session 1 completed (FC60 core exists)
- [ ] Terminal 3 Session 2 completed (Multi-user FC60 exists)

**Dependencies:**
- [ ] `anthropic` package installed (verify: `pip show anthropic`)
- [ ] `ANTHROPIC_API_KEY` environment variable set (verify: `echo $ANTHROPIC_API_KEY`)
- [ ] Claude API access confirmed (test API call succeeds)

**Files Required:**
- `/backend/oracle-service/app/engines/fc60.py` (from T3-S1)
- `/backend/oracle-service/app/engines/fc60_multi_user.py` (from T3-S2)
- `/backend/oracle-service/app/config.py` (API key configuration)

**Installation Commands:**
```bash
cd /backend/oracle-service
source venv/bin/activate
pip install anthropic==0.18.1 --break-system-packages
export ANTHROPIC_API_KEY="your_api_key_here"
```

---

## TOOLS TO USE

**Mandatory Tools:**
1. **view** - Read product-self-knowledge skill for Anthropic API best practices
2. **extended_thinking** - Design prompt templates and translation strategy
3. **Subagents** - Parallel creation (AI module + Translation module + Tests)

**Tool Usage:**
```bash
# Step 1: Read skill for API patterns
view /mnt/skills/public/product-self-knowledge/SKILL.md

# Step 2: Use extended_thinking for:
# - Prompt template design (balance mystical vs practical)
# - Translation strategy (preserve numerology terms)
# - Error handling (API failures, rate limits)

# Step 3: Coordinate subagents:
# Subagent 1: AI Interpretation module
# Subagent 2: Translation module  
# Subagent 3: Tests for both modules
```

---

## REQUIREMENTS

### Functional Requirements

#### 1. AI Interpretation Module

**Four Output Formats:**

**Format 1: Simple Explanation**
- Target audience: 5th grade reading level
- Use analogies and everyday examples
- No jargon, explain all numerology terms
- Example structure:
  ```
  Your FC60 signature is "Water Ox in Receptive Gate"
  
  Think of it like this: Water Ox is like being a calm, steady river that nourishes everything around it. You have the strength of an ox combined with water's ability to adapt and flow.
  
  The Receptive Gate means you're in a time for listening and receiving wisdom from the universe, like soil receiving seeds before spring.
  ```

**Format 2: Person-to-Person Advice**
- Conversational, empathetic tone
- Second-person ("you") addressing user directly
- Blend mystical wisdom with practical life advice
- Example structure:
  ```
  I see you're carrying the energy of Water Ox right now. This tells me you're in a phase where patience and steady effort will serve you better than rushing.
  
  The universe is asking you to be like water - powerful yet flexible. Don't fight against obstacles; flow around them. Your natural strength will carry you through.
  
  Trust your intuition during this Receptive Gate period. The answers you seek might come through quiet moments of reflection rather than active searching.
  ```

**Format 3: Action Steps**
- 3 concrete, actionable suggestions
- Specific and measurable
- Aligned with FC60 signature energy
- Example structure:
  ```
  Based on your Water Ox energy in Receptive Gate, here are 3 actions:
  
  1. Daily Practice: Spend 10 minutes each morning in quiet reflection or meditation. Water Ox energy needs stillness to recharge.
  
  2. Decision-Making: For major decisions this week, sleep on them for at least one night before acting. Your Receptive Gate phase favors patience.
  
  3. Relationships: Focus on listening more than speaking in conversations. Your current energy is about receiving wisdom from others.
  ```

**Format 4: Universe Message**
- Poetic, inspirational wisdom
- Third-person perspective (the universe speaking)
- Mystical language celebrating the signature
- Example structure:
  ```
  The universe whispers:
  
  "Dear soul of Water and Ox, you are the sacred river that knows when to rush and when to rest. In this Receptive Gate, the cosmos opens doors not through force but through surrender.
  
  Like the ox plowing fields in spring rain, your steady devotion creates fertile ground for miracles. Trust the divine timing. The seeds you plant in silence will bloom in perfect season.
  
  You are both the question and the answer, both the seeker and the found. Flow with grace, stand with strength, receive with open heart."
  ```

**Implementation Requirements:**
- Function signature: `interpret_fc60(signature: str, format: str, context: dict) -> str`
- Formats: `"simple"`, `"advice"`, `"actions"`, `"universe"`
- Context includes: user's question, timestamp, previous readings
- Cache responses for 1 hour (same signature + format)
- Fallback to basic explanation if API fails

#### 2. Multi-User AI Interpretation

**Individual Insights:**
- Separate interpretation for each user in group
- Highlights individual's unique role in group dynamic
- Example: "In this trio, you (Fire Horse) bring the spark and initiative..."

**Group Dynamics:**
- Overall synergy analysis
- Potential conflicts and resolutions
- Collective strengths
- Example: "This partnership combines Water Ox's patience with Fire Horse's passion and Wood Dragon's vision - a powerful triad for long-term projects"

**Partnership Guidance:**
- Compatibility score (0-100) with explanation
- Complementary energies identified
- Areas requiring attention
- Communication styles advice

**Implementation Requirements:**
- Function: `interpret_multi_user(users: List[dict], format: str) -> dict`
- Returns: `{"individual": [str, str, ...], "group": str, "compatibility": int, "guidance": str}`
- Uses FC60MultiUser from T3-S2 for compatibility calculation
- Includes all 4 interpretation formats for group reading

#### 3. Translation Service

**English → Persian:**
- Preserve numerology terminology accuracy
- Translate cultural references appropriately
- Maintain mystical tone in Persian
- Example: "Water Ox" → "گاو آب" (direct) or "گاو در جریان آب" (poetic)

**Persian → English:**
- Handle Persian numerology terms correctly
- Preserve user's question intent
- Cultural adaptation for Western context

**Batch Translation:**
- Process multiple texts in single API call
- Maintain order and context
- Example: Translate all 4 interpretation formats at once

**Context Preservation:**
- FC60 signature names translated consistently
- Hexagram meanings preserved
- Gate/Position terminology standardized
- Persian calendar references (e.g., Nowruz) explained in English

**Implementation Requirements:**
- Function: `translate(text: str, source_lang: str, target_lang: str, context: dict) -> str`
- Function: `batch_translate(texts: List[str], source_lang: str, target_lang: str) -> List[str]`
- Supported: `source_lang` and `target_lang` in `["en", "fa"]`
- Context includes: FC60 signature, numerology terms to preserve
- Cache translations for common terms

#### 4. Prompt Engineering

**Prompt Template Structure:**
```python
PROMPTS = {
    "simple": """
You are explaining FC60 numerology to someone who's never heard of it.

FC60 Signature: {signature}
Hexagram: {hexagram}
Element: {element}
Animal: {animal}
Gate: {gate_meaning}

User's Question: {user_question}

Explain this signature in simple terms a 5th grader could understand.
Use analogies and everyday examples. No jargon.

Keep it under 150 words. Be warm and encouraging.
""",
    
    "advice": """
You are a wise, empathetic advisor speaking directly to the user.

FC60 Signature: {signature}
Full Reading:
- Hexagram: {hexagram} - {hexagram_meaning}
- Element: {element} - {element_qualities}
- Animal: {animal} - {animal_traits}
- Gate: {gate_meaning}

User Context:
- Question: {user_question}
- Previous Readings: {previous_readings}
- Current Life Phase: {life_phase}

Provide person-to-person advice that blends mystical wisdom with practical life guidance.
Address them as "you" and speak from your wisdom as an advisor.

Keep it conversational and empathetic. 200-250 words.
""",
    
    "actions": """
Based on this FC60 signature, provide 3 specific, actionable steps.

FC60 Signature: {signature}
Energy Profile:
- Element: {element} - {element_energy}
- Animal: {animal} - {animal_energy}
- Current Gate: {gate_meaning}

User's Question: {user_question}

Generate 3 concrete actions aligned with this energy:

1. [Daily Practice] - Something they can do each day
2. [Decision-Making] - How to approach decisions this week
3. [Relationships] - Interpersonal action

Each action should be specific, measurable, and achievable within 7 days.
Format as numbered list with brief explanations.
""",
    
    "universe": """
You are the voice of the universe speaking poetic wisdom.

FC60 Signature: {signature}
Cosmic Alignment:
- {hexagram_full_meaning}
- {element_universe_connection}
- {animal_soul_message}

Write an inspirational universe message (3 short paragraphs):

Paragraph 1: Acknowledge their soul's journey with this signature
Paragraph 2: Mystical wisdom about their current energy
Paragraph 3: Divine timing and trust

Use poetic language. Third person perspective ("The universe sees...", "This soul carries...").
Be mystical, inspirational, and celebratory.

150-200 words total.
""",
    
    "multi_user_group": """
Analyze the group dynamics of these FC60 signatures:

{users_list}

Provide:
1. Individual Role: What each person brings to the group
2. Synergy Analysis: How energies combine or conflict
3. Collective Strengths: What this group excels at together
4. Areas of Attention: Potential challenges and how to navigate

Keep it balanced - acknowledge both harmony and growth areas.
250-300 words.
""",
    
    "translation_en_to_fa": """
Translate this FC60 numerology interpretation from English to Persian.

IMPORTANT RULES:
1. Preserve FC60 signature names exactly: "{signature}" remains "{signature}"
2. Translate numerology terms consistently:
   - "Hexagram" → "شش گوشه" or "هگزاگرام"
   - "Element" → "عنصر"
   - "Gate" → "دروازه" or "گیت"
3. Maintain mystical/spiritual tone in Persian
4. Adapt cultural references for Persian readers
5. Keep the same emotional tone and message intent

English Text:
{english_text}

FC60 Context:
- Signature: {signature}
- Numerology Terms: {numerology_terms}

Translate to Persian while preserving meaning and mystical quality.
""",
    
    "translation_fa_to_en": """
Translate this Persian text about FC60 numerology to English.

IMPORTANT RULES:
1. Preserve FC60 signature names
2. Translate numerology terms consistently (see mapping below)
3. Adapt Persian cultural references for Western readers
4. Maintain the mystical/spiritual tone

Persian Text:
{persian_text}

FC60 Context:
- Signature: {signature}
- Known Terms: {numerology_terms}

Common Persian → English terms:
- "گاو آب" → "Water Ox"
- "عنصر" → "Element"
- "شش گوشه" → "Hexagram"

Translate to English while preserving the spiritual essence.
"""
}
```

**Prompt Guidelines:**
- Include FC60 context without overwhelming
- Balance mystical wisdom with practical advice
- Provide examples in prompts to guide Claude
- Keep prompts under 500 tokens (leave room for response)
- Use clear structure (sections, bullet points)
- Specify word count limits

### Non-Functional Requirements

#### Performance
- AI interpretation response time: <3 seconds (p95)
- Translation response time: <2 seconds for single text
- Batch translation: <5 seconds for 4 texts
- Cache hit rate: >80% for common signatures
- API rate limit handling: Exponential backoff with max 3 retries

#### Security
- API key stored in environment variable (never in code)
- API key never logged (even in debug mode)
- User questions/context not stored permanently
- Sanitize all inputs before sending to Claude API
- Rate limiting: Max 100 requests/hour per user

#### Quality
- Test coverage: 95%+ for AI and translation modules
- Mock API responses for all tests (no real API calls in tests)
- Error messages user-friendly (no stack traces to user)
- Logging: JSON format with request_id for tracing
- All prompts validated (no injection vulnerabilities)

#### Cultural Sensitivity
- Persian translations reviewed by native speaker
- Avoid culturally inappropriate analogies
- Respect both Islamic and Zoroastrian contexts
- Gender-neutral language in all formats
- No assumptions about user's beliefs

---

## IMPLEMENTATION PLAN

### Phase 1: Setup & Configuration (Duration: 30 min)

**Tasks:**

1. **Install Dependencies**
   ```bash
   pip install anthropic==0.18.1 --break-system-packages
   pip install python-dotenv==1.0.0 --break-system-packages
   ```
   - Acceptance: `pip show anthropic` shows version 0.18.1

2. **Configure API Key**
   
   Create `/backend/oracle-service/app/config.py`:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   class Settings:
       ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
       AI_MODEL: str = "claude-sonnet-4-20250514"  # Claude Sonnet 4
       AI_MAX_TOKENS: int = 1000
       AI_TIMEOUT: int = 30  # seconds
       AI_CACHE_TTL: int = 3600  # 1 hour
       
       # Rate limiting
       AI_MAX_REQUESTS_PER_HOUR: int = 100
       
       # Translation
       SUPPORTED_LANGUAGES: list = ["en", "fa"]
   
   settings = Settings()
   
   # Validation
   if not settings.ANTHROPIC_API_KEY:
       raise ValueError("ANTHROPIC_API_KEY environment variable not set")
   ```
   - Acceptance: `python -c "from app.config import settings; print(settings.AI_MODEL)"` prints model name

3. **Create .env File**
   ```bash
   echo "ANTHROPIC_API_KEY=your_key_here" > /backend/oracle-service/.env
   ```
   - Acceptance: `.env` file exists and is in `.gitignore`

**Files to Create:**
- `/backend/oracle-service/app/config.py` (150 lines)
- `/backend/oracle-service/.env.example` (template)

**Verification:**
```bash
cd /backend/oracle-service
python -c "from app.config import settings; print(f'API Key: {settings.ANTHROPIC_API_KEY[:10]}...')"
# Expected: API Key: sk-ant-api...
```

**Checkpoint:**
- [ ] Dependencies installed
- [ ] API key configured and validated
- [ ] Config module imports without errors

**STOP if checkpoint fails - cannot proceed without API access**

---

### Phase 2: AI Interpretation Module (Duration: 90 min)

**Tasks:**

1. **Create Prompt Templates**

   Create `/backend/oracle-service/app/engines/prompts.py`:
   ```python
   """
   AI prompt templates for FC60 interpretations
   """
   from typing import Dict
   
   PROMPTS: Dict[str, str] = {
       "simple": """...""",  # Full prompts from requirements
       "advice": """...""",
       "actions": """...""",
       "universe": """...""",
       "multi_user_group": """...""",
   }
   
   def build_prompt(
       format_type: str,
       signature: str,
       context: dict
   ) -> str:
       """
       Build AI prompt from template
       
       Args:
           format_type: One of ["simple", "advice", "actions", "universe"]
           signature: FC60 signature (e.g., "Water Ox")
           context: Dict with hexagram, element, animal, user_question, etc.
       
       Returns:
           Formatted prompt ready for Claude API
       
       Raises:
           ValueError: If format_type invalid
       """
       if format_type not in PROMPTS:
           raise ValueError(f"Unknown format: {format_type}")
       
       prompt_template = PROMPTS[format_type]
       return prompt_template.format(
           signature=signature,
           **context
       )
   ```
   - Acceptance: `build_prompt("simple", "Water Ox", {...})` returns valid prompt string

2. **Create AI Client**

   Create `/backend/oracle-service/app/engines/ai_client.py`:
   ```python
   """
   Claude API client for AI interpretations
   """
   import asyncio
   import logging
   from typing import Optional, Dict, List
   from anthropic import Anthropic, AsyncAnthropic
   from app.config import settings
   from app.engines.prompts import build_prompt
   
   logger = logging.getLogger(__name__)
   
   class AIClient:
       """
       Client for Claude API with caching and error handling
       """
       
       def __init__(self):
           self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
           self.cache: Dict[str, str] = {}
           self.cache_ttl = settings.AI_CACHE_TTL
       
       async def interpret(
           self,
           signature: str,
           format_type: str,
           context: dict
       ) -> str:
           """
           Generate AI interpretation
           
           Args:
               signature: FC60 signature
               format_type: Interpretation format
               context: Additional context for prompt
           
           Returns:
               AI-generated interpretation
           
           Raises:
               ValueError: Invalid format
               TimeoutError: API timeout
               Exception: API error
           """
           # Check cache
           cache_key = f"{signature}:{format_type}"
           if cache_key in self.cache:
               logger.debug(f"Cache hit: {cache_key}")
               return self.cache[cache_key]
           
           # Build prompt
           prompt = build_prompt(format_type, signature, context)
           
           # Call API with timeout and retry
           try:
               response = await asyncio.wait_for(
                   self._call_api(prompt),
                   timeout=settings.AI_TIMEOUT
               )
               
               # Extract text
               interpretation = response.content[0].text
               
               # Cache result
               self.cache[cache_key] = interpretation
               
               logger.info(
                   "AI interpretation generated",
                   extra={
                       "signature": signature,
                       "format": format_type,
                       "response_length": len(interpretation)
                   }
               )
               
               return interpretation
               
           except asyncio.TimeoutError:
               logger.error("AI API timeout", extra={"signature": signature})
               raise TimeoutError(f"AI interpretation timed out after {settings.AI_TIMEOUT}s")
           
           except Exception as e:
               logger.error(
                   "AI API error",
                   extra={"signature": signature, "error": str(e)},
                   exc_info=True
               )
               # Fallback to basic explanation
               return self._fallback_interpretation(signature, format_type)
       
       async def _call_api(self, prompt: str):
           """Call Claude API with exponential backoff retry"""
           max_retries = 3
           for attempt in range(max_retries):
               try:
                   response = await self.client.messages.create(
                       model=settings.AI_MODEL,
                       max_tokens=settings.AI_MAX_TOKENS,
                       messages=[
                           {"role": "user", "content": prompt}
                       ]
                   )
                   return response
               
               except Exception as e:
                   if attempt == max_retries - 1:
                       raise
                   
                   # Exponential backoff
                   wait_time = 2 ** attempt
                   logger.warning(
                       f"AI API retry {attempt + 1}/{max_retries} after {wait_time}s",
                       extra={"error": str(e)}
                   )
                   await asyncio.sleep(wait_time)
       
       def _fallback_interpretation(
           self,
           signature: str,
           format_type: str
       ) -> str:
           """Fallback when API fails"""
           fallbacks = {
               "simple": f"Your FC60 signature is {signature}. This represents a unique energy pattern in the universe.",
               "advice": f"With {signature} energy, trust your intuition and stay aligned with your true nature.",
               "actions": f"Based on {signature}:\n1. Reflect daily\n2. Trust your instincts\n3. Stay balanced",
               "universe": f"The universe recognizes {signature} - a sacred pattern of cosmic wisdom."
           }
           return fallbacks.get(format_type, f"FC60 Signature: {signature}")
   ```
   - Acceptance: API call succeeds with test prompt

3. **Create Interpretation Service**

   Create `/backend/oracle-service/app/services/interpretation_service.py`:
   ```python
   """
   High-level service for AI interpretations
   """
   import logging
   from typing import Dict, List
   from app.engines.ai_client import AIClient
   from app.engines.fc60 import FC60Engine
   
   logger = logging.getLogger(__name__)
   
   class InterpretationService:
       """
       Service for generating AI-powered FC60 interpretations
       """
       
       def __init__(self):
           self.ai_client = AIClient()
           self.fc60_engine = FC60Engine()
       
       async def interpret_fc60(
           self,
           signature: str,
           format_type: str = "advice",
           user_question: str = "",
           previous_readings: List[str] = None
       ) -> str:
           """
           Generate AI interpretation of FC60 signature
           
           Args:
               signature: FC60 signature (e.g., "Water Ox")
               format_type: One of ["simple", "advice", "actions", "universe"]
               user_question: User's specific question (optional)
               previous_readings: Previous FC60 readings for context (optional)
           
           Returns:
               AI-generated interpretation in requested format
           
           Raises:
               ValueError: Invalid signature or format
           """
           # Validate format
           valid_formats = ["simple", "advice", "actions", "universe"]
           if format_type not in valid_formats:
               raise ValueError(f"Format must be one of {valid_formats}")
           
           # Decode FC60 to get full context
           fc60_data = self.fc60_engine.decode(signature)
           
           # Build context for AI
           context = {
               "hexagram": fc60_data["hexagram"],
               "hexagram_meaning": fc60_data["meaning"],
               "element": fc60_data["element"],
               "element_qualities": self._get_element_qualities(fc60_data["element"]),
               "animal": fc60_data["animal"],
               "animal_traits": self._get_animal_traits(fc60_data["animal"]),
               "gate_meaning": fc60_data.get("gate_meaning", ""),
               "user_question": user_question or "General guidance",
               "previous_readings": previous_readings or [],
           }
           
           # Generate interpretation
           interpretation = await self.ai_client.interpret(
               signature=signature,
               format_type=format_type,
               context=context
           )
           
           logger.info(
               "Interpretation generated",
               extra={
                   "signature": signature,
                   "format": format_type,
                   "has_question": bool(user_question)
               }
           )
           
           return interpretation
       
       def _get_element_qualities(self, element: str) -> str:
           """Get qualities for each element"""
           qualities = {
               "Water": "Flowing, adaptive, intuitive, deep emotions",
               "Wood": "Growing, creative, flexible, expansive",
               "Fire": "Passionate, transformative, energetic, illuminating",
               "Earth": "Grounding, stable, nurturing, practical",
               "Metal": "Sharp, precise, structured, refined"
           }
           return qualities.get(element, "")
       
       def _get_animal_traits(self, animal: str) -> str:
           """Get traits for each animal"""
           traits = {
               "Rat": "Quick-witted, resourceful, charming",
               "Ox": "Patient, reliable, strong-willed",
               "Tiger": "Brave, competitive, confident",
               "Rabbit": "Gentle, elegant, compassionate",
               "Dragon": "Powerful, lucky, ambitious",
               "Snake": "Wise, mysterious, intuitive",
               "Horse": "Free-spirited, energetic, independent",
               "Goat": "Creative, calm, gentle",
               "Monkey": "Clever, curious, playful",
               "Rooster": "Observant, hardworking, confident",
               "Dog": "Loyal, honest, protective",
               "Pig": "Generous, compassionate, diligent"
           }
           return traits.get(animal, "")
   ```
   - Acceptance: `interpret_fc60("Water Ox", "simple")` returns appropriate simple explanation

**Files to Create:**
- `/backend/oracle-service/app/engines/prompts.py` (300 lines)
- `/backend/oracle-service/app/engines/ai_client.py` (250 lines)
- `/backend/oracle-service/app/services/interpretation_service.py` (200 lines)

**Verification:**
```bash
cd /backend/oracle-service
python -c "
import asyncio
from app.services.interpretation_service import InterpretationService

async def test():
    service = InterpretationService()
    result = await service.interpret_fc60('Water Ox', 'simple')
    print(result[:100])

asyncio.run(test())
"
# Expected: AI-generated simple explanation (first 100 chars)
```

**Checkpoint:**
- [ ] Prompts build correctly
- [ ] AI client connects to Claude API
- [ ] Service generates all 4 interpretation formats
- [ ] Cache works (second call faster)
- [ ] Fallback works (when API disabled)

**STOP if checkpoint fails - fix AI integration before proceeding**

---

### Phase 3: Multi-User AI Interpretation (Duration: 60 min)

**Tasks:**

1. **Extend AI Client for Multi-User**

   Add to `/backend/oracle-service/app/engines/ai_client.py`:
   ```python
   async def interpret_multi_user(
       self,
       users: List[Dict],
       format_type: str = "advice"
   ) -> Dict[str, any]:
       """
       Generate multi-user interpretation
       
       Args:
           users: List of dicts with {name, signature, role}
           format_type: Interpretation format for group
       
       Returns:
           {
               "individual": [str, str, ...],
               "group": str,
               "compatibility": int,
               "guidance": str
           }
       """
       # Build users list string
       users_list = "\n".join([
           f"- {u['name']}: {u['signature']} ({u.get('role', 'Member')})"
           for u in users
       ])
       
       # Build prompt
       prompt = PROMPTS["multi_user_group"].format(
           users_list=users_list
       )
       
       # Call API
       response = await self._call_api(prompt)
       group_interpretation = response.content[0].text
       
       # Generate individual insights
       individual_insights = []
       for user in users:
           individual_prompt = f"""
           In a group with these signatures:
           {users_list}
           
           Focus on {user['name']} ({user['signature']}).
           What unique role do they play in this group dynamic?
           Keep it to 2-3 sentences.
           """
           
           individual_response = await self._call_api(individual_prompt)
           individual_insights.append(individual_response.content[0].text)
       
       return {
           "individual": individual_insights,
           "group": group_interpretation,
           "compatibility": self._calculate_compatibility(users),
           "guidance": self._extract_guidance(group_interpretation)
       }
   
   def _calculate_compatibility(self, users: List[Dict]) -> int:
       """
       Calculate group compatibility score (0-100)
       
       Uses FC60MultiUser compatibility from T3-S2
       """
       from app.engines.fc60_multi_user import FC60MultiUser
       
       multi_engine = FC60MultiUser()
       compatibility_matrix = multi_engine.calculate_compatibility([
           u['signature'] for u in users
       ])
       
       # Average of all pairwise compatibilities
       total = sum(sum(row) for row in compatibility_matrix)
       count = len(users) * (len(users) - 1)
       avg = total / count if count > 0 else 0
       
       return int(avg)
   
   def _extract_guidance(self, group_interpretation: str) -> str:
       """Extract key guidance from group interpretation"""
       # Simple heuristic: look for sentences with keywords
       keywords = ["should", "can", "focus", "attention", "important"]
       sentences = group_interpretation.split(".")
       
       guidance_sentences = [
           s.strip() + "."
           for s in sentences
           if any(kw in s.lower() for kw in keywords)
       ]
       
       return " ".join(guidance_sentences[:3])  # Top 3 guidance points
   ```
   - Acceptance: Multi-user interpretation returns all 4 fields

2. **Add to Interpretation Service**

   Add to `/backend/oracle-service/app/services/interpretation_service.py`:
   ```python
   async def interpret_group(
       self,
       users: List[Dict],
       format_type: str = "advice"
   ) -> Dict[str, any]:
       """
       Generate multi-user group interpretation
       
       Args:
           users: List of {name, signature, role}
           format_type: Format for group reading
       
       Returns:
           Multi-user interpretation dict
       
       Example:
           users = [
               {"name": "Alice", "signature": "Water Ox", "role": "Leader"},
               {"name": "Bob", "signature": "Fire Horse", "role": "Innovator"}
           ]
       """
       # Validate users
       if not users or len(users) < 2:
           raise ValueError("Need at least 2 users for group interpretation")
       
       # Generate multi-user interpretation
       result = await self.ai_client.interpret_multi_user(
           users=users,
           format_type=format_type
       )
       
       logger.info(
           "Group interpretation generated",
           extra={
               "user_count": len(users),
               "compatibility": result["compatibility"]
           }
       )
       
       return result
   ```
   - Acceptance: Group interpretation works for 2+ users

**Files Modified:**
- `/backend/oracle-service/app/engines/ai_client.py` (+150 lines)
- `/backend/oracle-service/app/services/interpretation_service.py` (+80 lines)

**Verification:**
```bash
python -c "
import asyncio
from app.services.interpretation_service import InterpretationService

async def test():
    service = InterpretationService()
    users = [
        {'name': 'Alice', 'signature': 'Water Ox'},
        {'name': 'Bob', 'signature': 'Fire Horse'}
    ]
    result = await service.interpret_group(users)
    print(f\"Compatibility: {result['compatibility']}\")
    print(f\"Individual insights: {len(result['individual'])}\")

asyncio.run(test())
"
# Expected: Compatibility score (0-100) and 2 individual insights
```

**Checkpoint:**
- [ ] Multi-user interpretation generates individual insights
- [ ] Group dynamics analysis returned
- [ ] Compatibility score calculated (0-100)
- [ ] Guidance extracted

**STOP if checkpoint fails**

---

### Phase 4: Translation Service (Duration: 90 min)

**Tasks:**

1. **Create Translation Client**

   Create `/backend/oracle-service/app/engines/translation_client.py`:
   ```python
   """
   Translation service using Claude API
   """
   import asyncio
   import logging
   from typing import List, Dict
   from anthropic import AsyncAnthropic
   from app.config import settings
   from app.engines.prompts import PROMPTS
   
   logger = logging.getLogger(__name__)
   
   class TranslationClient:
       """
       Client for English ↔ Persian translation with FC60 context
       """
       
       def __init__(self):
           self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
           self.cache: Dict[str, str] = {}
       
       async def translate(
           self,
           text: str,
           source_lang: str,
           target_lang: str,
           fc60_context: dict = None
       ) -> str:
           """
           Translate text with FC60 context preservation
           
           Args:
               text: Text to translate
               source_lang: Source language code ("en" or "fa")
               target_lang: Target language code ("en" or "fa")
               fc60_context: Dict with signature, numerology_terms
           
           Returns:
               Translated text
           
           Raises:
               ValueError: Unsupported language
           """
           # Validate languages
           if source_lang not in settings.SUPPORTED_LANGUAGES:
               raise ValueError(f"Unsupported source language: {source_lang}")
           if target_lang not in settings.SUPPORTED_LANGUAGES:
               raise ValueError(f"Unsupported target language: {target_lang}")
           
           # Check cache
           cache_key = f"{source_lang}:{target_lang}:{text[:50]}"
           if cache_key in self.cache:
               logger.debug(f"Translation cache hit")
               return self.cache[cache_key]
           
           # Build translation prompt
           fc60_context = fc60_context or {}
           
           if source_lang == "en" and target_lang == "fa":
               prompt = PROMPTS["translation_en_to_fa"].format(
                   english_text=text,
                   signature=fc60_context.get("signature", ""),
                   numerology_terms=fc60_context.get("numerology_terms", [])
               )
           elif source_lang == "fa" and target_lang == "en":
               prompt = PROMPTS["translation_fa_to_en"].format(
                   persian_text=text,
                   signature=fc60_context.get("signature", ""),
                   numerology_terms=fc60_context.get("numerology_terms", [])
               )
           else:
               raise ValueError(f"Translation {source_lang}→{target_lang} not supported")
           
           # Call API
           try:
               response = await asyncio.wait_for(
                   self.client.messages.create(
                       model=settings.AI_MODEL,
                       max_tokens=settings.AI_MAX_TOKENS,
                       messages=[{"role": "user", "content": prompt}]
                   ),
                   timeout=settings.AI_TIMEOUT
               )
               
               translation = response.content[0].text
               
               # Cache result
               self.cache[cache_key] = translation
               
               logger.info(
                   "Translation completed",
                   extra={
                       "source_lang": source_lang,
                       "target_lang": target_lang,
                       "text_length": len(text)
                   }
               )
               
               return translation
               
           except Exception as e:
               logger.error(
                   "Translation failed",
                   extra={"error": str(e)},
                   exc_info=True
               )
               raise
       
       async def batch_translate(
           self,
           texts: List[str],
           source_lang: str,
           target_lang: str,
           fc60_context: dict = None
       ) -> List[str]:
           """
           Translate multiple texts in one API call
           
           Args:
               texts: List of texts to translate
               source_lang: Source language
               target_lang: Target language
               fc60_context: FC60 context (optional)
           
           Returns:
               List of translated texts (same order)
           """
           # Build batch prompt
           numbered_texts = "\n\n".join([
               f"[{i+1}] {text}"
               for i, text in enumerate(texts)
           ])
           
           batch_prompt = f"""
           Translate these {len(texts)} texts from {source_lang} to {target_lang}.
           Preserve FC60 numerology terminology.
           
           Texts:
           {numbered_texts}
           
           Return translations in same format: [1] translation, [2] translation, etc.
           """
           
           try:
               response = await asyncio.wait_for(
                   self.client.messages.create(
                       model=settings.AI_MODEL,
                       max_tokens=settings.AI_MAX_TOKENS * 2,  # More tokens for batch
                       messages=[{"role": "user", "content": batch_prompt}]
                   ),
                   timeout=settings.AI_TIMEOUT * 2
               )
               
               # Parse response
               translation_text = response.content[0].text
               translations = self._parse_batch_response(translation_text, len(texts))
               
               logger.info(
                   "Batch translation completed",
                   extra={"count": len(texts), "source_lang": source_lang, "target_lang": target_lang}
               )
               
               return translations
               
           except Exception as e:
               logger.error("Batch translation failed", exc_info=True)
               # Fallback: translate individually
               return [
                   await self.translate(text, source_lang, target_lang, fc60_context)
                   for text in texts
               ]
       
       def _parse_batch_response(
           self,
           response_text: str,
           expected_count: int
       ) -> List[str]:
           """Parse numbered batch translation response"""
           import re
           
           # Find all [N] translation patterns
           pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)'
           matches = re.findall(pattern, response_text, re.DOTALL)
           
           translations = [text.strip() for _, text in matches]
           
           # Verify count
           if len(translations) != expected_count:
               logger.warning(
                   f"Batch translation count mismatch: expected {expected_count}, got {len(translations)}"
               )
           
           return translations
   ```
   - Acceptance: Single translation works, batch translation works

2. **Add Translation to Interpretation Service**

   Add to `/backend/oracle-service/app/services/interpretation_service.py`:
   ```python
   from app.engines.translation_client import TranslationClient
   
   class InterpretationService:
       def __init__(self):
           self.ai_client = AIClient()
           self.fc60_engine = FC60Engine()
           self.translator = TranslationClient()
       
       async def interpret_fc60_multilang(
           self,
           signature: str,
           format_type: str = "advice",
           language: str = "en",
           user_question: str = ""
       ) -> str:
           """
           Generate interpretation in specified language
           
           Args:
               signature: FC60 signature
               format_type: Interpretation format
               language: "en" or "fa"
               user_question: User's question
           
           Returns:
               Interpretation in requested language
           """
           # Generate in English first
           interpretation_en = await self.interpret_fc60(
               signature=signature,
               format_type=format_type,
               user_question=user_question
           )
           
           # Translate if needed
           if language == "fa":
               fc60_context = {
                   "signature": signature,
                   "numerology_terms": ["Hexagram", "Element", "Animal", "Gate"]
               }
               
               interpretation = await self.translator.translate(
                   text=interpretation_en,
                   source_lang="en",
                   target_lang="fa",
                   fc60_context=fc60_context
               )
           else:
               interpretation = interpretation_en
           
           return interpretation
       
       async def interpret_fc60_all_formats_multilang(
           self,
           signature: str,
           language: str = "en"
       ) -> Dict[str, str]:
           """
           Generate all 4 formats in specified language
           
           Returns:
               {
                   "simple": str,
                   "advice": str,
                   "actions": str,
                   "universe": str
               }
           """
           formats = ["simple", "advice", "actions", "universe"]
           
           # Generate all in English
           interpretations_en = {}
           for fmt in formats:
               interpretations_en[fmt] = await self.interpret_fc60(
                   signature=signature,
                   format_type=fmt
               )
           
           # Batch translate if Persian requested
           if language == "fa":
               fc60_context = {"signature": signature}
               
               translations = await self.translator.batch_translate(
                   texts=list(interpretations_en.values()),
                   source_lang="en",
                   target_lang="fa",
                   fc60_context=fc60_context
               )
               
               interpretations = dict(zip(formats, translations))
           else:
               interpretations = interpretations_en
           
           return interpretations
   ```
   - Acceptance: Persian interpretations returned correctly

**Files to Create:**
- `/backend/oracle-service/app/engines/translation_client.py` (250 lines)

**Files Modified:**
- `/backend/oracle-service/app/services/interpretation_service.py` (+100 lines)

**Verification:**
```bash
python -c "
import asyncio
from app.services.interpretation_service import InterpretationService

async def test():
    service = InterpretationService()
    
    # Test single translation
    result_en = await service.interpret_fc60('Water Ox', 'simple', language='en')
    print('English:', result_en[:50])
    
    result_fa = await service.interpret_fc60('Water Ox', 'simple', language='fa')
    print('Persian:', result_fa[:50])
    
    # Test batch
    all_formats = await service.interpret_fc60_all_formats_multilang('Water Ox', 'fa')
    print(f\"Formats translated: {len(all_formats)}\")

asyncio.run(test())
"
# Expected: English interpretation, Persian interpretation (RTL), 4 formats
```

**Checkpoint:**
- [ ] Single text translation works (en → fa)
- [ ] Single text translation works (fa → en)
- [ ] Batch translation works (4 formats at once)
- [ ] FC60 terms preserved in translation
- [ ] Persian text shows RTL correctly

**STOP if checkpoint fails**

---

### Phase 5: Testing (Duration: 90 min)

**Tasks:**

1. **Create Test Fixtures**

   Create `/backend/oracle-service/tests/fixtures/ai_responses.json`:
   ```json
   {
       "simple_water_ox": "Your FC60 signature is Water Ox in Receptive Gate. Think of it like being a calm, steady river that nourishes everything around it...",
       "advice_water_ox": "I see you're carrying the energy of Water Ox right now. This tells me you're in a phase where patience and steady effort will serve you better than rushing...",
       "actions_water_ox": "Based on your Water Ox energy:\n1. Daily Practice: Spend 10 minutes each morning in quiet reflection...",
       "universe_water_ox": "The universe whispers: Dear soul of Water and Ox, you are the sacred river...",
       "multi_user_group": "This partnership combines Water Ox's patience with Fire Horse's passion...",
       "translation_en_to_fa": "امضای FC60 شما گاو آب است...",
       "translation_fa_to_en": "Your FC60 signature is Water Ox..."
   }
   ```

2. **Create AI Client Tests**

   Create `/backend/oracle-service/tests/test_ai_client.py`:
   ```python
   """
   Tests for AI client
   """
   import pytest
   import asyncio
   from unittest.mock import Mock, AsyncMock, patch
   from app.engines.ai_client import AIClient
   
   @pytest.fixture
   def mock_anthropic_response():
       """Mock Claude API response"""
       mock = Mock()
       mock.content = [Mock(text="Mocked AI interpretation")]
       return mock
   
   @pytest.mark.asyncio
   async def test_interpret_simple_format(mock_anthropic_response):
       """Test simple format interpretation"""
       with patch('app.engines.ai_client.AsyncAnthropic') as mock_client:
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_anthropic_response)
           
           client = AIClient()
           result = await client.interpret(
               signature="Water Ox",
               format_type="simple",
               context={"hexagram": "Test", "element": "Water"}
           )
           
           assert result == "Mocked AI interpretation"
           assert mock_client.return_value.messages.create.called
   
   @pytest.mark.asyncio
   async def test_interpret_cache_hit():
       """Test caching works"""
       with patch('app.engines.ai_client.AsyncAnthropic') as mock_client:
           mock_response = Mock()
           mock_response.content = [Mock(text="Cached result")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = AIClient()
           
           # First call
           result1 = await client.interpret("Water Ox", "simple", {})
           
           # Second call (should hit cache)
           result2 = await client.interpret("Water Ox", "simple", {})
           
           assert result1 == result2
           assert mock_client.return_value.messages.create.call_count == 1  # Only called once
   
   @pytest.mark.asyncio
   async def test_interpret_timeout():
       """Test timeout handling"""
       with patch('app.engines.ai_client.AsyncAnthropic') as mock_client:
           # Simulate slow API
           async def slow_call(*args, **kwargs):
               await asyncio.sleep(100)
           
           mock_client.return_value.messages.create = slow_call
           
           client = AIClient()
           
           with pytest.raises(TimeoutError):
               await client.interpret("Water Ox", "simple", {})
   
   @pytest.mark.asyncio
   async def test_interpret_fallback_on_error():
       """Test fallback when API fails"""
       with patch('app.engines.ai_client.AsyncAnthropic') as mock_client:
           mock_client.return_value.messages.create = AsyncMock(side_effect=Exception("API Error"))
           
           client = AIClient()
           result = await client.interpret("Water Ox", "simple", {})
           
           # Should return fallback
           assert "Water Ox" in result
           assert len(result) > 0
   
   @pytest.mark.asyncio
   async def test_multi_user_interpretation():
       """Test multi-user interpretation"""
       with patch('app.engines.ai_client.AsyncAnthropic') as mock_client:
           mock_response = Mock()
           mock_response.content = [Mock(text="Group interpretation")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = AIClient()
           users = [
               {"name": "Alice", "signature": "Water Ox"},
               {"name": "Bob", "signature": "Fire Horse"}
           ]
           
           result = await client.interpret_multi_user(users)
           
           assert "individual" in result
           assert "group" in result
           assert "compatibility" in result
           assert len(result["individual"]) == 2
   ```

3. **Create Translation Tests**

   Create `/backend/oracle-service/tests/test_translation.py`:
   ```python
   """
   Tests for translation client
   """
   import pytest
   from unittest.mock import Mock, AsyncMock, patch
   from app.engines.translation_client import TranslationClient
   
   @pytest.mark.asyncio
   async def test_translate_en_to_fa():
       """Test English to Persian translation"""
       with patch('app.engines.translation_client.AsyncAnthropic') as mock_client:
           mock_response = Mock()
           mock_response.content = [Mock(text="امضای شما گاو آب است")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = TranslationClient()
           result = await client.translate(
               text="Your signature is Water Ox",
               source_lang="en",
               target_lang="fa",
               fc60_context={"signature": "Water Ox"}
           )
           
           assert len(result) > 0
           # Persian text (RTL)
           assert any(ord(c) > 1000 for c in result)  # Persian characters
   
   @pytest.mark.asyncio
   async def test_translate_fa_to_en():
       """Test Persian to English translation"""
       with patch('app.engines.translation_client.AsyncAnthropic') as mock_client:
           mock_response = Mock()
           mock_response.content = [Mock(text="Water Ox")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = TranslationClient()
           result = await client.translate(
               text="گاو آب",
               source_lang="fa",
               target_lang="en"
           )
           
           assert "Water Ox" in result
   
   @pytest.mark.asyncio
   async def test_batch_translate():
       """Test batch translation"""
       with patch('app.engines.translation_client.AsyncAnthropic') as mock_client:
           mock_response = Mock()
           mock_response.content = [Mock(text="[1] ترجمه اول\n[2] ترجمه دوم\n[3] ترجمه سوم")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = TranslationClient()
           texts = ["Text 1", "Text 2", "Text 3"]
           
           results = await client.batch_translate(
               texts=texts,
               source_lang="en",
               target_lang="fa"
           )
           
           assert len(results) == 3
   
   @pytest.mark.asyncio
   async def test_translation_preserves_fc60_terms():
       """Test FC60 terms not translated"""
       with patch('app.engines.translation_client.AsyncAnthropic') as mock_client:
           # Mock response should preserve "Water Ox"
           mock_response = Mock()
           mock_response.content = [Mock(text="امضای شما Water Ox است")]
           mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)
           
           client = TranslationClient()
           result = await client.translate(
               text="Your signature is Water Ox",
               source_lang="en",
               target_lang="fa",
               fc60_context={"signature": "Water Ox"}
           )
           
           assert "Water Ox" in result  # Preserved
   ```

4. **Create Integration Tests**

   Create `/backend/oracle-service/tests/test_interpretation_service.py`:
   ```python
   """
   Integration tests for interpretation service
   """
   import pytest
   from unittest.mock import patch, AsyncMock, Mock
   from app.services.interpretation_service import InterpretationService
   
   @pytest.mark.asyncio
   async def test_interpret_all_formats():
       """Test generating all 4 formats"""
       with patch('app.services.interpretation_service.AIClient') as mock_ai:
           mock_ai.return_value.interpret = AsyncMock(return_value="Mocked interpretation")
           
           service = InterpretationService()
           
           formats = ["simple", "advice", "actions", "universe"]
           for fmt in formats:
               result = await service.interpret_fc60("Water Ox", format_type=fmt)
               assert len(result) > 0
   
   @pytest.mark.asyncio
   async def test_interpret_with_user_question():
       """Test interpretation with user question"""
       with patch('app.services.interpretation_service.AIClient') as mock_ai:
           mock_ai.return_value.interpret = AsyncMock(return_value="Interpretation")
           
           service = InterpretationService()
           result = await service.interpret_fc60(
               signature="Water Ox",
               user_question="Should I change jobs?"
           )
           
           assert len(result) > 0
   
   @pytest.mark.asyncio
   async def test_interpret_group():
       """Test group interpretation"""
       with patch('app.services.interpretation_service.AIClient') as mock_ai:
           mock_result = {
               "individual": ["Alice insight", "Bob insight"],
               "group": "Group dynamics",
               "compatibility": 85,
               "guidance": "Work together"
           }
           mock_ai.return_value.interpret_multi_user = AsyncMock(return_value=mock_result)
           
           service = InterpretationService()
           users = [
               {"name": "Alice", "signature": "Water Ox"},
               {"name": "Bob", "signature": "Fire Horse"}
           ]
           
           result = await service.interpret_group(users)
           
           assert len(result["individual"]) == 2
           assert result["compatibility"] > 0
   
   @pytest.mark.asyncio
   async def test_multilang_interpretation():
       """Test interpretation in Persian"""
       with patch('app.services.interpretation_service.AIClient') as mock_ai:
           with patch('app.services.interpretation_service.TranslationClient') as mock_trans:
               mock_ai.return_value.interpret = AsyncMock(return_value="English interpretation")
               mock_trans.return_value.translate = AsyncMock(return_value="ترجمه فارسی")
               
               service = InterpretationService()
               result = await service.interpret_fc60_multilang(
                   signature="Water Ox",
                   language="fa"
               )
               
               # Should be Persian
               assert any(ord(c) > 1000 for c in result)
   
   @pytest.mark.asyncio
   async def test_batch_multilang_all_formats():
       """Test all 4 formats in Persian"""
       with patch('app.services.interpretation_service.AIClient') as mock_ai:
           with patch('app.services.interpretation_service.TranslationClient') as mock_trans:
               mock_ai.return_value.interpret = AsyncMock(return_value="English")
               mock_trans.return_value.batch_translate = AsyncMock(return_value=[
                   "ساده", "توصیه", "اقدامات", "پیام کیهانی"
               ])
               
               service = InterpretationService()
               result = await service.interpret_fc60_all_formats_multilang(
                   signature="Water Ox",
                   language="fa"
               )
               
               assert len(result) == 4
               assert "simple" in result
               assert "advice" in result
   ```

5. **Run All Tests**
   ```bash
   cd /backend/oracle-service
   pytest tests/test_ai_client.py -v
   pytest tests/test_translation.py -v
   pytest tests/test_interpretation_service.py -v
   pytest tests/ --cov=app.engines.ai_client --cov=app.engines.translation_client --cov=app.services.interpretation_service
   ```
   - Acceptance: 95%+ coverage, all tests pass

**Files to Create:**
- `/backend/oracle-service/tests/fixtures/ai_responses.json` (50 lines)
- `/backend/oracle-service/tests/test_ai_client.py` (200 lines)
- `/backend/oracle-service/tests/test_translation.py` (150 lines)
- `/backend/oracle-service/tests/test_interpretation_service.py` (180 lines)

**Verification:**
```bash
cd /backend/oracle-service
pytest tests/ -v --cov
# Expected: 25+ tests pass, 95%+ coverage
```

**Checkpoint:**
- [ ] All AI client tests pass
- [ ] All translation tests pass
- [ ] All service integration tests pass
- [ ] Coverage ≥95%
- [ ] No API calls in tests (all mocked)

**STOP if checkpoint fails**

---

## VERIFICATION CHECKLIST

### Code Quality
- [ ] Type hints on all functions (mypy strict passes)
- [ ] Docstrings on all public functions
- [ ] Error handling (no bare except, proper exceptions)
- [ ] Logging (JSON format, appropriate levels)
- [ ] No API key in code (environment variable only)
- [ ] No sensitive data logged

### Testing
- [ ] 95%+ test coverage (pytest --cov)
- [ ] All tests pass (25+ tests)
- [ ] Mocked API responses (no real API calls)
- [ ] Edge cases covered (timeout, errors, cache)
- [ ] Integration tests for all formats

### Functionality
- [ ] All 4 interpretation formats work
- [ ] Multi-user interpretation works (2+ users)
- [ ] Translation en→fa works
- [ ] Translation fa→en works
- [ ] Batch translation works (4 texts)
- [ ] Caching works (second call faster)
- [ ] Fallback works (API disabled)

### Performance
- [ ] AI interpretation <3s (p95)
- [ ] Translation <2s (single text)
- [ ] Batch translation <5s (4 texts)
- [ ] Cache hit rate >80% (after warmup)

### Cultural Appropriateness
- [ ] Persian translations reviewed (native speaker if available)
- [ ] No culturally inappropriate analogies
- [ ] FC60 terms preserved in translation
- [ ] Gender-neutral language
- [ ] Mystical tone maintained

### Security
- [ ] API key in environment variable only
- [ ] API key never logged
- [ ] Input sanitization (prevent injection)
- [ ] Rate limiting implemented
- [ ] No user data stored permanently

---

## SUCCESS CRITERIA

1. **AI Interpretation Quality**
   - [ ] Simple format readable by 5th grader (Flesch-Kincaid <6.0)
   - [ ] Advice format empathetic and conversational
   - [ ] Action steps concrete and measurable
   - [ ] Universe message poetic and inspirational

2. **Multi-User Insights**
   - [ ] Individual insights unique for each user
   - [ ] Group dynamics analysis cohesive
   - [ ] Compatibility score calculated (0-100)
   - [ ] Guidance actionable

3. **Translation Accuracy**
   - [ ] FC60 signatures preserved exactly
   - [ ] Numerology terms consistent
   - [ ] Cultural context adapted appropriately
   - [ ] Mystical tone maintained

4. **Performance Targets**
   - [ ] API response time <3s (p95)
   - [ ] Cache hit rate >80%
   - [ ] Error rate <1%
   - [ ] Rate limit never exceeded

5. **Integration Success**
   - [ ] Works with T3-S1 (FC60 Core)
   - [ ] Works with T3-S2 (Multi-user FC60)
   - [ ] Ready for T2 API integration
   - [ ] All tests pass in CI/CD

---

## HANDOFF TO NEXT SESSION

If session ends mid-implementation:

**Resume from Phase:** [Current phase number]

**Context needed:**
- API key configured and tested
- Which phases completed (checkpoints passed)
- Any known issues or blockers

**Verification before continuing:**
```bash
# Verify Phase N-1 completed
cd /backend/oracle-service
pytest tests/test_[previous_phase].py -v
# Expected: All tests pass
```

**Files created so far:**
- List all files with line counts
- Note any incomplete files

**Next immediate step:**
[Exact task to resume from]

---

## NEXT STEPS (After This Spec)

1. **Terminal 2 Session 4: API Integration**
   - Create FastAPI endpoints for AI interpretations
   - Add `/api/oracle/interpret` endpoint (all 4 formats)
   - Add `/api/oracle/interpret-group` endpoint (multi-user)
   - Add `/api/oracle/translate` endpoint
   - Tests: 95%+ coverage

2. **Terminal 1 Session 5: Frontend Oracle Page**
   - Create Oracle.tsx page
   - Interpretation format selector (4 formats)
   - Multi-user input form
   - Language toggle (English/Persian)
   - Display AI-generated wisdom

3. **Terminal 3 Session 4: Performance Optimization**
   - Benchmark AI interpretation speed
   - Optimize prompt lengths
   - Implement advanced caching
   - Add response streaming (if needed)

---

## APPENDIX: Claude API Best Practices

**From product-self-knowledge skill:**

1. **Model Selection:**
   - Use `claude-sonnet-4-20250514` for balance of quality and speed
   - Use `claude-opus-4-5-20251101` only for complex reasoning
   - Use `claude-haiku-4-5-20251001` for simple translations

2. **Token Management:**
   - Simple interpretation: 200-300 tokens
   - Advice format: 400-500 tokens
   - Multi-user: 600-800 tokens
   - Translation: 300-400 tokens

3. **Error Handling:**
   - Always use asyncio.wait_for with timeout
   - Implement exponential backoff (2^n seconds)
   - Max 3 retries before fallback
   - Log all API errors with request_id

4. **Rate Limiting:**
   - Respect tier limits (check Anthropic dashboard)
   - Implement client-side rate limiter
   - Cache aggressively to reduce calls
   - Batch when possible

5. **Prompt Engineering:**
   - Be specific about format and length
   - Provide examples in prompts
   - Use clear structure (sections, bullets)
   - Include context without overwhelming

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Estimated Total Duration: 4-5 hours*  
*Claude Code CLI Ready: Yes*  
*Extended Thinking: Enabled*
