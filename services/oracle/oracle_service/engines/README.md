# Oracle Engines

Active engine modules in `services/oracle/oracle_service/engines/`.

All engines are **production code** with active importers. None are legacy.

---

## Engine Index

| Module                   | Purpose                      | Key Exports                                                                                                            |
| ------------------------ | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `ai_client.py`           | Anthropic SDK wrapper        | `generate()`, `is_available()`, `clear_cache()`                                                                        |
| `ai_engine.py`           | Scanner-focused AI functions | `brain_strategy_recommendation()`, `brain_mid_session_analysis()`, `brain_session_summary()`, `analyze_scan_pattern()` |
| `ai_interpreter.py`      | Reading AI interpretation    | AI-powered reading text generation                                                                                     |
| `config.py`              | Engine configuration         | Settings and constants                                                                                                 |
| `errors.py`              | Custom exception classes     | Engine-specific error types                                                                                            |
| `events.py`              | Event system                 | Event publishing and subscription                                                                                      |
| `health.py`              | Health check                 | Service health status                                                                                                  |
| `learner.py`             | Learning/feedback engine     | `recalculate_learning_metrics()`, `generate_prompt_emphasis()`                                                         |
| `learning.py`            | Learning data models         | Learning statistics and tracking                                                                                       |
| `logger.py`              | Structured logging           | JSON logging setup (imports `notifier`)                                                                                |
| `memory.py`              | Scanner memory               | Cross-session pattern memory                                                                                           |
| `multi_user_service.py`  | Multi-user readings          | Compatibility readings for multiple users                                                                              |
| `notifier.py`            | Telegram notifications       | Bot commands, alerts, inline keyboards (imports `vault`)                                                               |
| `oracle.py`              | Core Oracle logic            | Main reading orchestration                                                                                             |
| `prompt_templates.py`    | AI prompt templates          | System prompts for reading generation                                                                                  |
| `scanner_brain.py`       | Adaptive scanner brain       | Strategy selection, key generation (imports `ai_engine`)                                                               |
| `security.py`            | Oracle-level security        | Encryption helpers for Oracle data                                                                                     |
| `session_manager.py`     | Session management           | User session lifecycle                                                                                                 |
| `timing_advisor.py`      | Timing guidance              | Moon phase, ganzhi cycle timing                                                                                        |
| `translation_service.py` | Persian translation          | EN/FA translation                                                                                                      |
| `vault.py`               | Secure key storage           | Encrypted vault for private keys                                                                                       |

## Dependency Graph (Key Imports)

```
scanner_brain.py --> ai_engine.py --> ai_client.py (Anthropic SDK)
logger.py --> notifier.py --> vault.py
learner.py (imported by api/app/routers/learning.py — documented exception)
```

## AI Call Chain

All AI calls flow through the Anthropic Python SDK:

```
scanner_brain.py
    --> ai_engine.py (scanner-specific prompts)
        --> ai_client.py (SDK wrapper)
            --> Anthropic HTTP API

oracle.py / ai_interpreter.py
    --> ai_client.py (reading prompts)
        --> Anthropic HTTP API
```

No subprocess calls. No CLI invocations. SDK only.
