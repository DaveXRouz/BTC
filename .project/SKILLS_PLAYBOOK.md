# SKILLS PLAYBOOK - NPS V4

## 🎯 PURPOSE

This playbook provides comprehensive guidance on when and how to use Claude's skills for NPS V4 development. Skills are pre-built best practices that dramatically improve output quality.

**Rule #1:** ALWAYS check for applicable skills BEFORE writing code.  
**Rule #2:** Read the SKILL.md file completely before using the skill.  
**Rule #3:** Follow skill patterns exactly - they're battle-tested.

---

## 📋 SKILLS INVENTORY

### Public Skills (Production-Ready)

| Skill | Path | Use When | Output |
|-------|------|----------|--------|
| **docx** | `/mnt/skills/public/docx/` | Creating Word documents | .docx files |
| **pdf** | `/mnt/skills/public/pdf/` | Creating/manipulating PDFs | .pdf files |
| **pptx** | `/mnt/skills/public/pptx/` | Creating presentations | .pptx files |
| **xlsx** | `/mnt/skills/public/xlsx/` | Creating spreadsheets | .xlsx files |
| **frontend-design** | `/mnt/skills/public/frontend-design/` | Building web UIs | HTML/React/CSS |
| **product-self-knowledge** | `/mnt/skills/public/product-self-knowledge/` | Anthropic API integration | API code |

### Example Skills (Advanced Patterns)

| Skill | Path | Use When | Output |
|-------|------|----------|--------|
| **doc-coauthoring** | `/mnt/skills/examples/doc-coauthoring/` | Writing specs/docs collaboratively | MD files |
| **web-artifacts-builder** | `/mnt/skills/examples/web-artifacts-builder/` | Complex multi-component web apps | React artifacts |
| **skill-creator** | `/mnt/skills/examples/skill-creator/` | Creating new skills | SKILL.md |
| **theme-factory** | `/mnt/skills/examples/theme-factory/` | Styling artifacts with themes | Themed output |
| **mcp-builder** | `/mnt/skills/examples/mcp-builder/` | Building MCP servers | MCP server code |
| **canvas-design** | `/mnt/skills/examples/canvas-design/` | Creating visual art/posters | .png/.pdf |
| **brand-guidelines** | `/mnt/skills/examples/brand-guidelines/` | Applying Anthropic branding | Branded content |
| **slack-gif-creator** | `/mnt/skills/examples/slack-gif-creator/` | Creating animated GIFs | .gif files |
| **algorithmic-art** | `/mnt/skills/examples/algorithmic-art/` | Generative art with code | p5.js code |

---

## 🔍 SKILL SELECTION DECISION TREE

```
START
  ↓
What are you creating?
  ↓
┌─────────────────────────────────────────────────────────┐
│ DOCUMENTS                                               │
├─────────────────────────────────────────────────────────┤
│ Word doc? → docx skill                                  │
│ PDF? → pdf skill                                        │
│ Presentation? → pptx skill                              │
│ Spreadsheet? → xlsx skill                               │
│ Technical spec? → doc-coauthoring skill                 │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ WEB INTERFACES                                          │
├─────────────────────────────────────────────────────────┤
│ Simple React component? → frontend-design skill         │
│ Complex multi-page app? → web-artifacts-builder skill   │
│ Need theming? → frontend-design + theme-factory         │
│ Anthropic branding? → Add brand-guidelines skill        │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ API/INTEGRATION                                         │
├─────────────────────────────────────────────────────────┤
│ Using Anthropic API? → product-self-knowledge skill     │
│ Building MCP server? → mcp-builder skill                │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ VISUAL/CREATIVE                                         │
├─────────────────────────────────────────────────────────┤
│ Poster/static design? → canvas-design skill             │
│ Animated GIF? → slack-gif-creator skill                 │
│ Generative art? → algorithmic-art skill                 │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ META                                                    │
├─────────────────────────────────────────────────────────┤
│ Creating a new skill? → skill-creator skill             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 NPS V4 SPECIFIC SKILL MAPPINGS

### Layer 1 - Frontend

**Scenario:** Creating React dashboard page

**Skills to use:**
1. **Primary:** `frontend-design` - Modern, production-grade UI
2. **Optional:** `theme-factory` - Apply dark theme matching V3
3. **Optional:** `brand-guidelines` - If using Anthropic colors

**Workflow:**
```bash
view /mnt/skills/public/frontend-design/SKILL.md
view /mnt/skills/examples/theme-factory/SKILL.md (if theming)

# Then create component following patterns
```

**Example prompt after reading skills:**
```
Using frontend-design skill patterns, create Dashboard.tsx with:
- Multi-terminal cards showing scanner status
- Real-time WebSocket updates
- Dark theme (V3 aesthetic)
- Health dots for service status
```

---

### Layer 2 - API

**Scenario:** Integrating Claude API for Oracle service

**Skills to use:**
1. **Primary:** `product-self-knowledge` - Anthropic API details
2. **Optional:** `mcp-builder` - If creating MCP server

**Workflow:**
```bash
view /mnt/skills/public/product-self-knowledge/SKILL.md

# Verify current API capabilities, models, pricing
```

**Example prompt after reading skill:**
```
Using product-self-knowledge skill, integrate Claude API for pattern analysis:
- Model: Claude Sonnet 4.5
- Streaming: Yes
- Function calling: For structured outputs
- Error handling: Retry with exponential backoff
```

---

### Layer 3 - Backend

**Scenario:** Building MCP server for Scanner service

**Skills to use:**
1. **Primary:** `mcp-builder` - High-quality MCP server patterns

**Workflow:**
```bash
view /mnt/skills/examples/mcp-builder/SKILL.md

# Follow FastMCP or MCP SDK patterns
```

**Example prompt after reading skill:**
```
Using mcp-builder skill, create Scanner MCP server with:
- Tools: start_scan, stop_scan, get_stats
- Resources: Current scan state
- Prompts: Scanner configuration templates
```

---

### Documentation Tasks

**Scenario:** Writing V4 API documentation

**Skills to use:**
1. **Primary:** `doc-coauthoring` - Structured workflow

**Workflow:**
```bash
view /mnt/skills/examples/doc-coauthoring/SKILL.md

# Follow structured co-authoring workflow
```

**Example prompt after reading skill:**
```
Using doc-coauthoring skill, create API_REFERENCE.md:
- Transfer context about V4 endpoints
- Refine with examples and edge cases
- Verify with user scenarios
```

---

## 📦 SKILL COMBINATION PATTERNS

### Pattern 1: Frontend + Theme

**Use case:** Creating branded web interface

**Skills:**
1. `frontend-design` (base UI)
2. `theme-factory` (styling)
3. `brand-guidelines` (Anthropic colors) [optional]

**Workflow:**
```bash
# Step 1: Read all skills
view /mnt/skills/public/frontend-design/SKILL.md
view /mnt/skills/examples/theme-factory/SKILL.md
view /mnt/skills/examples/brand-guidelines/SKILL.md

# Step 2: Create base UI with frontend-design patterns
# Step 3: Apply theme using theme-factory
# Step 4: Add Anthropic brand colors if needed
```

**Result:** Production-quality branded UI

---

### Pattern 2: Documentation + Collaboration

**Use case:** Writing technical specifications

**Skills:**
1. `doc-coauthoring` (workflow)
2. `docx` or `pdf` (output format)

**Workflow:**
```bash
# Step 1: Use doc-coauthoring for content structure
view /mnt/skills/examples/doc-coauthoring/SKILL.md

# Step 2: Use docx for final document
view /mnt/skills/public/docx/SKILL.md
```

**Result:** Well-structured, professional document

---

### Pattern 3: API + MCP

**Use case:** Building API-integrated MCP server

**Skills:**
1. `product-self-knowledge` (API integration)
2. `mcp-builder` (MCP patterns)

**Workflow:**
```bash
# Step 1: Verify API capabilities
view /mnt/skills/public/product-self-knowledge/SKILL.md

# Step 2: Build MCP server
view /mnt/skills/examples/mcp-builder/SKILL.md
```

**Result:** MCP server that uses Anthropic API correctly

---

## ⚠️ COMMON MISTAKES TO AVOID

### Mistake 1: Not Reading the Skill

**❌ Wrong:**
```
"Create a PowerPoint presentation about NPS V4"
[Proceeds without reading pptx skill]
```

**✅ Correct:**
```
view /mnt/skills/public/pptx/SKILL.md
[Reads skill completely]
"Using pptx skill patterns, create presentation about NPS V4 with:
- Title slide
- Architecture diagram
- Layer breakdown
- 7-terminal workflow
[Following exact skill structure]"
```

**Why it matters:** Skills contain battle-tested patterns that avoid common pitfalls.

---

### Mistake 2: Using Wrong Skill

**❌ Wrong:**
```
"Create API documentation"
[Uses generic approach instead of doc-coauthoring skill]
```

**✅ Correct:**
```
view /mnt/skills/examples/doc-coauthoring/SKILL.md
"Using doc-coauthoring skill workflow:
Phase 1: Transfer context
Phase 2: Refine content
Phase 3: Verify with scenarios"
```

**Why it matters:** Wrong skill = suboptimal output.

---

### Mistake 3: Ignoring Skill Combinations

**❌ Wrong:**
```
"Create a themed web UI"
[Uses only frontend-design, ignores theme-factory]
```

**✅ Correct:**
```
view /mnt/skills/public/frontend-design/SKILL.md
view /mnt/skills/examples/theme-factory/SKILL.md
"Using frontend-design + theme-factory:
1. Build UI components (frontend-design)
2. Apply dark theme (theme-factory)
3. Verify responsive design"
```

**Why it matters:** Combinations unlock advanced capabilities.

---

## 🎓 SKILL USAGE CHECKLIST

Before starting ANY task involving file creation:

- [ ] Identify task type (document, web UI, API, etc.)
- [ ] Check skills inventory for applicable skills
- [ ] Use `view` tool to read relevant SKILL.md files
- [ ] Understand skill patterns and examples
- [ ] Follow skill structure exactly
- [ ] Combine skills if needed
- [ ] Verify output matches skill quality standards

---

## 📊 SKILL EFFECTIVENESS MATRIX

| Task | Without Skill | With Skill | Improvement |
|------|---------------|------------|-------------|
| Word doc | Generic formatting | Professional TOC + headers | 5x better |
| Presentation | Basic slides | Engaging layouts + visuals | 10x better |
| React UI | Functional but generic | Production-grade design | 8x better |
| API integration | Trial and error | Correct from start | 3x faster |
| MCP server | Basic structure | High-quality with tools | 6x better |
| Documentation | Unstructured | Clear workflow + examples | 4x better |

---

## 🔄 SKILL UPDATE PROCESS

Skills evolve. When working on NPS V4:

**If you discover a new pattern:**
1. Document it clearly
2. Test it thoroughly
3. Use `skill-creator` skill to create new skill
4. Add to this playbook

**If a skill doesn't fit:**
1. Understand why (context mismatch? outdated?)
2. Adapt skill pattern to NPS V4 context
3. Document adaptation
4. Update this playbook

---

## 📚 QUICK REFERENCE

**Most Common NPS V4 Skills:**

| Task | Skill | Command |
|------|-------|---------|
| React component | frontend-design | `view /mnt/skills/public/frontend-design/SKILL.md` |
| API docs | doc-coauthoring | `view /mnt/skills/examples/doc-coauthoring/SKILL.md` |
| Claude API | product-self-knowledge | `view /mnt/skills/public/product-self-knowledge/SKILL.md` |
| MCP server | mcp-builder | `view /mnt/skills/examples/mcp-builder/SKILL.md` |
| Spec document | docx | `view /mnt/skills/public/docx/SKILL.md` |
| Presentation | pptx | `view /mnt/skills/public/pptx/SKILL.md` |

---

**Remember:** Skills are your superpower. Use them religiously. 🚀

*Version: 1.0*  
*Last Updated: 2026-02-08*
