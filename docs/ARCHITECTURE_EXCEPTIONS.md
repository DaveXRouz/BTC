# Architecture Exceptions

Documented intentional deviations from NPS architecture rules.

---

## Exception 1: Direct gRPC Import in `api/app/routers/learning.py`

**Rule violated:** Architecture Rule #1 — "API is the gateway. Frontend/Telegram only talk to FastAPI. Never directly to gRPC services."

**Location:** `api/app/routers/learning.py:255`

```python
@router.post(
    "/oracle/recalculate",
    response_model=OracleLearningStatsResponse,
    dependencies=[Depends(require_scope("oracle:admin"))],
)
async def recalculate_learning(db: Session = Depends(get_db)):
    from services.oracle.oracle_service.engines.learner import (
        generate_prompt_emphasis,
        recalculate_learning_metrics,
    )
    recalculate_learning_metrics(db)
    generate_prompt_emphasis(db)
    db.commit()
    return await get_oracle_learning_stats(db)
```

**Why it exists:** The `recalculate_learning` endpoint is an admin-only maintenance function that triggers Oracle learning recalculation. It imports directly from the Oracle engine layer (`learner.py`) rather than going through gRPC.

**Why it's acceptable:**

1. **Admin-only access** — Protected by `require_scope("oracle:admin")`, limiting to trusted operators.
2. **Maintenance operation** — Not a user-facing feature; triggered manually for learning model updates.
3. **Same-process optimization** — The API and Oracle share a Python process in the current deployment. Adding gRPC round-trip for an admin maintenance call adds complexity without security or separation benefit.
4. **No data sensitivity** — The function recalculates aggregate learning metrics, not user-specific sensitive data.

**Risk assessment:** Low. The import is scoped to a protected admin endpoint. The learner functions operate on aggregate database data and do not expose Oracle internals to unauthorized callers.

**Review trigger:** If the Oracle service moves to a separate process/container, this import must be replaced with a gRPC call to maintain service isolation.

---

## How to Add New Exceptions

1. Number sequentially (Exception 2, 3, ...)
2. State the rule being violated
3. Give exact file and line number
4. Explain why it exists and why it's acceptable
5. Document the risk level and review trigger
