# NPS Frontend

## Overview

The NPS frontend layer provides two interfaces:

1. **React Web UI** (`src/`) — Primary interface built with React, TypeScript, and Tailwind CSS (Vite build).
2. **Legacy Tkinter GUI** (`desktop-gui/legacy/`) — Legacy desktop GUI preserved as migration reference.

## React Web UI

### Tech Stack

- **React 18** + TypeScript
- **Tailwind CSS** for styling
- **Vite** for build and dev server
- **WebSocket** for real-time scanner updates

### Pages

| Page      | Route       | Description                                 |
| --------- | ----------- | ------------------------------------------- |
| Dashboard | `/`         | Real-time multi-terminal command center     |
| Scanner   | `/scanner`  | Scanner controls with live progress         |
| Oracle    | `/oracle`   | Oracle readings, question mode, name cipher |
| Vault     | `/vault`    | Encrypted findings browser                  |
| Learning  | `/learning` | AI learning center, XP/level tracking       |
| Settings  | `/settings` | Configuration, Telegram, security           |

### Directory Structure

```
src/
  pages/          — 6 page components
  components/     — Shared UI (Layout, StatsCard, LogPanel)
  services/       — API client (api.ts) + WebSocket (websocket.ts)
  types/          — TypeScript types mirroring Pydantic models
  i18n/           — Internationalization (EN, stubs for ES/FR)
```

### Key Commands

```bash
# Development server (port 5173)
npm run dev

# Production build
npm run build

# Type checking
npx tsc --noEmit
```

### Architecture Notes

- Frontend communicates **only** with the FastAPI gateway (`api/`).
- Never calls scanner or oracle gRPC services directly.
- WebSocket connection provides real-time scanner progress, findings, and health updates.
- All sensitive data (private keys, seeds) stays server-side; frontend only displays masked values.

## Legacy Desktop GUI

See `desktop-gui/legacy/README.md` for the legacy Tkinter GUI reference files and the dual-GUI migration strategy.
