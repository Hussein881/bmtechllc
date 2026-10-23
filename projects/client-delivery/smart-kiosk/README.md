# Smart Kiosk

Local edge-first kiosk prototype. The kiosk browser talks only to the local
Fastify edge service, which owns SQLite persistence, server-side pricing,
orders, and deterministic mock payment, kitchen, and POS adapters.

The current build is a demo foundation. It does not process cards or send
orders to live payment, kitchen, or POS systems.

## Prerequisites

- Node.js 22+
- pnpm 10+

## Run locally

```bash
pnpm install
pnpm dev
```

Open `http://localhost:5173`. The edge service runs at
`http://127.0.0.1:3001` and creates its seeded SQLite database at
`apps/edge-server/data/smart-kiosk.sqlite` by default.

Copy `.env.example` to `.env` to override edge host, port, database path, or
kiosk origin. Environment variables are read by the edge service; the client
uses `VITE_EDGE_URL` when it must point at another local edge address.

## Verification

```bash
pnpm typecheck
pnpm build
pnpm lint
pnpm test
```

## Current implementation

- Seeded breakfast and lunch schedules, categories, menu items, and a modifier.
- SQLite migration ledger (`schema_migrations`) and foreign-key enforcement.
- Server-authoritative pricing, order creation, transaction idempotency, and
  transaction-time snapshots.
- Clearly labelled mock payment outcomes and persisted mock kitchen/POS
  dispatch outcomes.
- Basic browser kiosk with schedule/category navigation, cart totals, checkout,
  simulated payment controls, high contrast, and lower-screen mode.

## Deliberately deferred

Real payment terminals, live POS/KDS/printer connections, encrypted payment
store-and-forward, cloud menu synchronization, and client checkout while the
Store Edge Node is unreachable require separately selected and verified
integrations.
