# frontend

Minimal React + Vite SPA for the fiap-secure-systems platform.

## Local development

- `make front-dev` — start the Vite dev server on `:5173` against the running gateway-service
- `make front-test` — Vitest unit tests
- `make front-build` — production build to `frontend/dist/`
- `make front-up` — run the production-built bundle in the compose stack
- `make front-round-trip` — headless register → upload → REPORT_READY assertion via curl + wscat

## Environment

The two values that matter are read at **build time** by Vite:

- `VITE_GATEWAY_BASE_URL` — public REST base, defaults to `http://localhost:8080`
- `VITE_GATEWAY_WS_URL` — WebSocket base, defaults to `ws://localhost:8080`

Override them in `.env` before running `npm run build` to point at a different gateway deployment.
