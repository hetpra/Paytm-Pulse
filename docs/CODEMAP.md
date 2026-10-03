# Code map

## Entry points

- backend/app/main.py: create_app factory, lifespan, health endpoint, and extension loading.
- backend/app/routes.py: frozen core HTTP contract and shared risk_view.
- backend/app/graph.py: LangGraph analysis, approval and execution workflow.
- frontend/src/App.jsx: mobile dashboard shell and extension slots.

## Extension framework (E0)

- backend/app/ext discovers opt-in packages and exposes safe filters/events plus an isolated namespace store.
- frontend/src/features discovers feature packages and renders only server-enabled slots/tabs.
- EXT_ENABLED=none leaves the core unchanged; all is the default; a comma list selects individual flags.

## Intentional deviations from the original manual

- The existing core defaults to the in-memory repo and deterministic/template LLM fallback for a reliable demo.
- E0 is additive: no extension package ships yet, so api/features returns an empty enabled list.
